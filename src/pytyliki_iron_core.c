#include "reaper/pytyliki_iron_core.h"
#include <stdio.h>
#include <string.h>
#define ARRAY_COUNT(items) (sizeof(items) / sizeof((items)[0]))
static const ReaperIronMarkerInfo marker_catalog[REAPER_IRON_MARKER_COUNT] = {
 {"module.begin","begin iron )",REAPER_IRON_CLASS_FRAMING,0},
 {"core.context","() core --",REAPER_IRON_CLASS_CONTEXT,1},
 {"system.context","[ system ]-",REAPER_IRON_CLASS_CONTEXT,1},
 {"block.end","stop option ;",REAPER_IRON_CLASS_FRAMING,0},
 {"level.context","] level .",REAPER_IRON_CLASS_CONTEXT,1},
 {"selection.filter","{ selective /",REAPER_IRON_CLASS_PLAN,1},
 {"operation.unit","} operation P)-",REAPER_IRON_CLASS_PLAN,1},
 {"work.massive","?? massive <>",REAPER_IRON_CLASS_PLAN,1},
 {"startup.plan","< start >?",REAPER_IRON_CLASS_PLAN,1},
 {"work.spawn.plan","grown new-work >/",REAPER_IRON_CLASS_PLAN,1},
 {"implementation.binding","> concrete //*",REAPER_IRON_CLASS_PLAN,1},
 {"utility.helper","## utility _",REAPER_IRON_CLASS_PLAN,1},
 {"layout.unify","# unify TAB",REAPER_IRON_CLASS_PLAN,1},
 {"branchpass.plan","setup brachpass ^^",REAPER_IRON_CLASS_PLAN,1},
 {"tournament.rank","!+ hyper tournament ^",REAPER_IRON_CLASS_PLAN,1},
 {"consistency.rules","CC based rules ^^^",REAPER_IRON_CLASS_POLICY,0},
 {"execution.jump.plan","level jump to run *(",REAPER_IRON_CLASS_PLAN,1},
 {"logic.true_connective","TRUE connective *+",REAPER_IRON_CLASS_PLAN,1},
 {"module.version","verison ///. *",REAPER_IRON_CLASS_SOURCE_METADATA,0},
 {"source.verification_claim","verificated /// !!",REAPER_IRON_CLASS_SOURCE_METADATA,0}
};
static int reject(ReaperIronError *error,size_t index,const char *message){
 if(error){error->block_index=index;(void)snprintf(error->message,sizeof error->message,"%s",message);}
 return 0;
}
static int valid_label(const char *label){
 size_t n=0u;if(!label||!label[0])return 0;
 while(label[n]){unsigned char c=(unsigned char)label[n];
  int ok=(c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='.'||c=='-';
  if(!ok||n>=REAPER_IRON_MAX_LABEL-1u)return 0;++n;
 }
 return 1;
}
size_t reaper_iron_marker_catalog(const ReaperIronMarkerInfo **out){
 if(out)*out=marker_catalog;return ARRAY_COUNT(marker_catalog);
}
const ReaperIronMarkerInfo *reaper_iron_marker_by_id(const char *id){
 size_t i;if(!id)return NULL;
 for(i=0;i<ARRAY_COUNT(marker_catalog);++i)if(strcmp(marker_catalog[i].semantic_id,id)==0)return &marker_catalog[i];
 return NULL;
}
const char *reaper_iron_semantic_class_name(ReaperIronSemanticClass c){
 switch(c){case REAPER_IRON_CLASS_FRAMING:return "framing";case REAPER_IRON_CLASS_CONTEXT:return "context";
 case REAPER_IRON_CLASS_PLAN:return "plan";case REAPER_IRON_CLASS_POLICY:return "policy";
 case REAPER_IRON_CLASS_SOURCE_METADATA:return "source-metadata";default:return "invalid";}
}
int reaper_iron_import(const ReaperIronImport *in,ReaperIronModule *out,ReaperIronError *error){
 size_t i;
 if(error){error->block_index=0u;error->message[0]='\0';}
 if(!in||!out)return reject(error,0u,"import input and output are required");
 if(in->schema_version!=REAPER_IRON_AST_VERSION)return reject(error,0u,"unsupported Pytyliki Iron Core AST version");
 if(!in->source_bytes||in->source_bytes>REAPER_IRON_MAX_SOURCE_BYTES)return reject(error,0u,"source byte length is outside the v1 bound");
 if(!valid_label(in->version_label))return reject(error,0u,"version label is missing or invalid");
 if(!valid_label(in->verification_claim))return reject(error,0u,"verification claim is missing or invalid");
 if(!in->policy_declarations)return reject(error,0u,"consistency policy declaration is required");
 if(!in->blocks||!in->block_count||in->block_count>REAPER_IRON_MAX_BLOCKS)return reject(error,0u,"block collection is empty or exceeds the v1 bound");
 memset(out,0,sizeof(*out));out->source_bytes=in->source_bytes;
 (void)snprintf(out->version_label,sizeof out->version_label,"%s",in->version_label);
 (void)snprintf(out->verification_claim,sizeof out->verification_claim,"%s",in->verification_claim);
 out->source_claim_only=1;out->typed_lowering_performed=0;out->execution_performed=0;out->hardware_effects_performed=0;
 for(i=0;i<in->block_count;++i){
  const ReaperIronBlockRef *b=&in->blocks[i];const ReaperIronMarkerInfo *m=reaper_iron_marker_by_id(b->semantic_id);
  const ReaperIronSourceAnchor *s=&b->source;uint64_t body_end;
  if(!m||!m->opens_block)return reject(error,i,"unknown semantic ID or non-block marker");
  if(!b->closed)return reject(error,i,"unclosed source block is not importable");
  if(!s->line||s->start_offset>s->body_offset||s->body_offset>s->end_offset||
     s->body_offset>in->source_bytes||s->body_length>in->source_bytes-s->body_offset||
     s->end_offset>in->source_bytes)return reject(error,i,"source anchor is outside the source document");
  body_end=s->body_offset+s->body_length;
  if(body_end!=s->end_offset)return reject(error,i,"source body length does not match its end offset");
  out->nodes[i].marker=m;out->nodes[i].source=*s;++out->node_count;
 }
 return 1;
}
