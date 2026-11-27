#include "reaper/pytyliki_iron_core.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static void test_catalog(void){
 const ReaperIronMarkerInfo *items=NULL;
 assert(reaper_iron_marker_catalog(&items)==REAPER_IRON_MARKER_COUNT);
 assert(items&&reaper_iron_marker_by_id("core.context"));
 assert(reaper_iron_marker_by_id("source.verification_claim"));
 assert(!reaper_iron_marker_by_id("privilege.grant"));
 assert(strcmp(reaper_iron_semantic_class_name(REAPER_IRON_CLASS_PLAN),"plan")==0);
}
static void test_import_preserves_source_anchors(void){
 const ReaperIronBlockRef blocks[]={
  {"core.context",{64u,77u,22u,99u,4u},1},
  {"selection.filter",{100u,117u,41u,158u,8u},1}
 };
 const ReaperIronImport in={REAPER_IRON_AST_VERSION,220u,"IRON_V1","SOURCE_CLAIM_ONLY",1u,blocks,2u};
 ReaperIronModule out;ReaperIronError error;
 assert(reaper_iron_import(&in,&out,&error));assert(out.node_count==2u);
 assert(out.nodes[0].source.start_offset==64u&&out.nodes[0].source.body_offset==77u);
 assert(out.nodes[0].source.end_offset==99u&&out.nodes[0].source.line==4u);
 assert(out.nodes[1].marker->semantic_class==REAPER_IRON_CLASS_PLAN);
 assert(out.source_claim_only==1&&!out.typed_lowering_performed&&!out.execution_performed&&!out.hardware_effects_performed);
 assert(strcmp(out.version_label,"IRON_V1")==0);
}
static void test_rejects_invalid_structure(void){
 ReaperIronModule out;ReaperIronError error;
 ReaperIronBlockRef b={"core.context",{8u,16u,8u,24u,2u},1};
 ReaperIronImport in={REAPER_IRON_AST_VERSION,64u,"V1","CLAIM",1u,&b,1u};
 assert(reaper_iron_import(&in,&out,&error));
 in.schema_version=99u;assert(!reaper_iron_import(&in,&out,&error)&&strstr(error.message,"unsupported"));
 in.schema_version=1u;b.semantic_id="privilege.grant";
 assert(!reaper_iron_import(&in,&out,&error)&&strstr(error.message,"unknown semantic ID"));
 b.semantic_id="core.context";b.closed=0;
 assert(!reaper_iron_import(&in,&out,&error)&&strstr(error.message,"unclosed"));
 b.closed=1;b.source.end_offset=23u;
 assert(!reaper_iron_import(&in,&out,&error)&&strstr(error.message,"body length"));
 b.source.end_offset=80u;
 assert(!reaper_iron_import(&in,&out,&error)&&strstr(error.message,"outside"));
}
static void test_requires_policy_and_labels(void){
 ReaperIronModule out;ReaperIronError error;
 ReaperIronBlockRef b={"system.context",{1u,3u,4u,7u,1u},1};
 ReaperIronImport in={1u,16u,"V1","CLAIM",0u,&b,1u};
 assert(!reaper_iron_import(&in,&out,&error)&&strstr(error.message,"policy"));
 in.policy_declarations=1u;in.version_label="";
 assert(!reaper_iron_import(&in,&out,&error)&&strstr(error.message,"version label"));
}
int main(void){test_catalog();test_import_preserves_source_anchors();test_rejects_invalid_structure();test_requires_policy_and_labels();puts("Reaper Pytyliki Iron Core bridge tests passed");return 0;}
