#include "reaper/ast.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { const ReaperTokenArray *tokens; size_t pos; unsigned depth; ReaperAst *ast; ReaperParseError *error; } Parser;
static int set_error(Parser *p,const char *message){if(p->error){const ReaperToken *t=&p->tokens->items[p->pos < p->tokens->length ? p->pos : p->tokens->length-1];(void)snprintf(p->error->message,sizeof p->error->message,"%s",message);p->error->line=t->line;p->error->column=t->column;}return 0;}
static const ReaperToken *peek(Parser *p){return p->pos<p->tokens->length?&p->tokens->items[p->pos]:NULL;}
static int token_is(Parser *p,const char *s){const ReaperToken *t=peek(p);return t&&strcmp(t->text,s)==0;}
static uint32_t add_node(Parser *p,ReaperAstKind kind,const char *text,uint32_t left,uint32_t right,size_t line,size_t column){
 if(p->ast->length>=UINT32_MAX)return REAPER_AST_NO_NODE;
 if(p->ast->length==p->ast->capacity){size_t n=p->ast->capacity?p->ast->capacity*2:16;if(n<p->ast->capacity||n>SIZE_MAX/sizeof *p->ast->items)return REAPER_AST_NO_NODE;ReaperAstNode *v=realloc(p->ast->items,n*sizeof *v);if(!v)return REAPER_AST_NO_NODE;p->ast->items=v;p->ast->capacity=n;}
 size_t n=text?strlen(text):0;char *copy=malloc(n+1);if(!copy)return REAPER_AST_NO_NODE;if(n)memcpy(copy,text,n);copy[n]='\0';
 uint32_t id=(uint32_t)p->ast->length++;p->ast->items[id]=(ReaperAstNode){kind,left,right,copy,line,column};return id;
}
static int precedence(const char *s){
 if(!strcmp(s,"::"))return 1;
 if(!strcmp(s,"??"))return 2;
 if(!strcmp(s,"or")||!strcmp(s,"||"))return 3;
 if(!strcmp(s,"and")||!strcmp(s,"&&"))return 4;
 if(!strcmp(s,"==")||!strcmp(s,"!="))return 5;
 if(!strcmp(s,"<")||!strcmp(s,">")||!strcmp(s,"<=")||!strcmp(s,">="))return 6;
 if(!strcmp(s,"+")||!strcmp(s,"-")||!strcmp(s,"+%")||!strcmp(s,"+|"))return 7;
 if(!strcmp(s,"*")||!strcmp(s,"/")||!strcmp(s,"%"))return 8;
 if(!strcmp(s,"**"))return 9;
 return 0;
}
static uint32_t parse_bp(Parser *p,int min_bp);
static uint32_t parse_primary(Parser *p){
 const ReaperToken *t=peek(p);if(!t)return REAPER_AST_NO_NODE;
 if(token_is(p,"-")||token_is(p,"+")||token_is(p,"!")||token_is(p,"not")){
  char op[16];size_t n=strlen(t->text);if(n>=sizeof op)return REAPER_AST_NO_NODE;memcpy(op,t->text,n+1);size_t line=t->line,col=t->column;++p->pos;
  uint32_t rhs=parse_bp(p,10);if(rhs==REAPER_AST_NO_NODE)return rhs;
  uint32_t id=add_node(p,REAPER_AST_UNARY,op,rhs,REAPER_AST_NO_NODE,line,col);if(id==REAPER_AST_NO_NODE)set_error(p,"out of memory building AST");return id;
 }
 if(token_is(p,"(")){++p->pos;uint32_t id=parse_bp(p,1);if(id==REAPER_AST_NO_NODE)return id;if(!token_is(p,")")){set_error(p,"expected ')' to close expression");return REAPER_AST_NO_NODE;}++p->pos;return id;}
 ReaperAstKind kind;
 if(t->kind==REAPER_TOK_CATALOG_OPERATOR){set_error(p,"catalogue operator is reserved; executable semantics are not registered");return REAPER_AST_NO_NODE;}
 if(t->kind==REAPER_TOK_NUMBER)kind=strchr(t->text,'.')?REAPER_AST_DECIMAL:REAPER_AST_INTEGER;
 else if(t->kind==REAPER_TOK_STRING)kind=REAPER_AST_STRING;
 else if(t->kind==REAPER_TOK_IDENTIFIER)kind=REAPER_AST_IDENTIFIER;
 else if(t->kind==REAPER_TOK_KEYWORD&&(!strcmp(t->text,"true")||!strcmp(t->text,"false")))kind=REAPER_AST_BOOLEAN;
 else if(t->kind==REAPER_TOK_KEYWORD&&!strcmp(t->text,"nothing"))kind=REAPER_AST_NULL;
 else{set_error(p,"expected a literal, identifier, or parenthesized expression");return REAPER_AST_NO_NODE;}
 uint32_t id=add_node(p,kind,t->text,REAPER_AST_NO_NODE,REAPER_AST_NO_NODE,t->line,t->column);if(id==REAPER_AST_NO_NODE){set_error(p,"out of memory building AST");return id;}++p->pos;return id;
}
static uint32_t parse_bp(Parser *p,int min_bp){
 if(++p->depth>REAPER_PARSE_MAX_DEPTH){--p->depth;set_error(p,"expression nesting limit exceeded");return REAPER_AST_NO_NODE;}
 uint32_t lhs=parse_primary(p);if(lhs==REAPER_AST_NO_NODE){--p->depth;return lhs;}
 for(;;){const ReaperToken *op=peek(p);if(!op)break;if(op->kind==REAPER_TOK_CATALOG_OPERATOR){set_error(p,"catalogue operator is reserved; executable semantics are not registered");--p->depth;return REAPER_AST_NO_NODE;}int bp=precedence(op->text);if(bp<min_bp||bp==0)break;
  char *name=malloc(strlen(op->text)+1);if(!name){set_error(p,"out of memory parsing operator");--p->depth;return REAPER_AST_NO_NODE;}strcpy(name,op->text);size_t line=op->line,col=op->column;++p->pos;
  int next=bp+(!strcmp(name,"**")?0:1);uint32_t rhs=parse_bp(p,next);if(rhs==REAPER_AST_NO_NODE){free(name);--p->depth;return rhs;}
  uint32_t both=add_node(p,REAPER_AST_BINARY,name,lhs,rhs,line,col);free(name);if(both==REAPER_AST_NO_NODE){set_error(p,"out of memory building AST");--p->depth;return both;}lhs=both;
 }
 --p->depth;return lhs;
}
int reaper_parse_expression(const ReaperTokenArray *tokens,ReaperAst *out,ReaperParseError *error){
 if(!out||!tokens||!tokens->items||tokens->length==0){if(error){snprintf(error->message,sizeof error->message,"tokens and output are required");error->line=1;error->column=1;}return 0;}
 memset(out,0,sizeof *out);out->root=REAPER_AST_NO_NODE;if(error)memset(error,0,sizeof *error);Parser p={tokens,0,0,out,error};
 out->root=parse_bp(&p,1);if(out->root==REAPER_AST_NO_NODE){reaper_ast_free(out);return 0;}
 while(p.pos<tokens->length&&tokens->items[p.pos].kind==REAPER_TOK_NEWLINE)++p.pos;
 if(p.pos>=tokens->length||tokens->items[p.pos].kind!=REAPER_TOK_EOF){set_error(&p,"unexpected token after expression");reaper_ast_free(out);return 0;}return 1;
}
void reaper_ast_free(ReaperAst *ast){if(!ast)return;for(size_t i=0;i<ast->length;++i)free(ast->items[i].text);free(ast->items);memset(ast,0,sizeof *ast);ast->root=REAPER_AST_NO_NODE;}
const char *reaper_ast_kind_name(ReaperAstKind k){switch(k){case REAPER_AST_INTEGER:return "integer";case REAPER_AST_DECIMAL:return "decimal";case REAPER_AST_STRING:return "string";case REAPER_AST_BOOLEAN:return "boolean";case REAPER_AST_NULL:return "null";case REAPER_AST_IDENTIFIER:return "identifier";case REAPER_AST_UNARY:return "unary";case REAPER_AST_BINARY:return "binary";default:return "invalid";}}
