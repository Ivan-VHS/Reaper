#ifdef NDEBUG
#undef NDEBUG
#endif
#include "reaper/elf64_linker.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static uint16_t read16(const uint8_t *p) { return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8u)); }
static uint32_t read32(const uint8_t *p) {
    uint32_t x = 0u; for (unsigned i = 0u; i < 4u; ++i) x |= (uint32_t)p[i] << (i * 8u); return x;
}
static uint64_t read64(const uint8_t *p) {
    uint64_t x = 0u; for (unsigned i = 0u; i < 8u; ++i) x |= (uint64_t)p[i] << (i * 8u); return x;
}
static void test_static_link_and_pc32_relocation(void) {
    static const uint8_t caller[] = {0xe8,0,0,0,0,0xb8,60,0,0,0,0x31,0xff,0x0f,0x05};
    static const uint8_t callee[] = {0x31,0xc0,0xc3};
    const ReaperElf64Section asec[] = {{".text",1u,6u,16u,0u,caller,sizeof caller}};
    const ReaperElf64Section bsec[] = {{".text",1u,6u,16u,0u,callee,sizeof callee}};
    const ReaperElf64Symbol asym[] = {
        {"_start",0u,0u,sizeof caller,1u,2u,0u},
        {"helper",REAPER_ELF64_NO_SECTION,0u,0u,1u,0u,0u}
    };
    const ReaperElf64Symbol bsym[] = {{"helper",0u,0u,sizeof callee,1u,2u,0u}};
    const ReaperElf64Relocation arel[] = {{0u,1u,1u,REAPER_ELF64_R_X86_64_PC32,-4}};
    const ReaperElf64Object objects[] = {
        {asec,1u,asym,2u,arel,1u},
        {bsec,1u,bsym,1u,NULL,0u}
    };
    ReaperElf64Executable output = {0};
    ReaperElf64Error error = {0};
    assert(reaper_elf64_link_executable(objects,2u,"_start",&output,&error)==REAPER_ELF64_OK);
    assert(output.data != NULL && output.size > 4096u);
    assert(memcmp(output.data,"\x7f" "ELF",4u)==0);
    assert(read16(output.data+16u)==2u && read16(output.data+18u)==62u);
    assert(read16(output.data+56u)==4u && output.entry_address==read64(output.data+24u));
    uint64_t text_offset=read64(output.data+64u+56u+8u);
    assert((int32_t)read32(output.data+(size_t)text_offset+1u)==11);
    reaper_elf64_executable_destroy(&output);
    assert(output.data==NULL && output.size==0u);
}
static void test_unresolved_symbol_fails(void) {
    static const uint8_t code[]={0xe8,0,0,0,0,0xc3};
    const ReaperElf64Section sec={".text",1u,6u,1u,0u,code,sizeof code};
    const ReaperElf64Symbol sym[]={
        {"_start",0u,0u,sizeof code,1u,2u,0u},
        {"missing",REAPER_ELF64_NO_SECTION,0u,0u,1u,0u,0u}
    };
    const ReaperElf64Relocation rel={0u,1u,1u,REAPER_ELF64_R_X86_64_PC32,-4};
    const ReaperElf64Object object={&sec,1u,sym,2u,&rel,1u};
    ReaperElf64Executable output={0}; ReaperElf64Error error={0};
    assert(reaper_elf64_link_executable(&object,1u,"_start",&output,&error)==REAPER_ELF64_UNRESOLVED_SYMBOL);
    assert(output.data==NULL);
}
int main(void) {
    test_static_link_and_pc32_relocation();
    test_unresolved_symbol_fails();
    puts("ELF64 static linker tests passed");
    return 0;
}
