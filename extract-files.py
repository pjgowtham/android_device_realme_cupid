#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from extract_utils.fixups_blob import (
    BlobFixupCtx,
    File,
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)
from extract_utils.tools import (
    llvm_objdump_path,
)
from extract_utils.utils import (
    run_cmd,
)

namespace_imports = [
    'hardware/oplus',
    'vendor/oneplus/sm8350-common',
    'vendor/qcom/opensource/display',
]


def blob_fixup_nop_call(
    ctx: BlobFixupCtx,
    file: File,
    file_path: str,
    call_instruction: str,
    disassemble_symbol: str,
    symbol: str,
    *args,
    **kwargs,
):
    for line in run_cmd(
        [
            llvm_objdump_path,
            f'--disassemble-symbols={disassemble_symbol}',
            file_path,
        ]
    ).splitlines():
        line = line.split(maxsplit=3)

        if len(line) != 4:
            continue

        offset, _, instruction, args = line

        if instruction != call_instruction:
            continue

        if not args.endswith(f' <{symbol}>'):
            continue

        with open(file_path, 'rb+') as f:
            f.seek(int(offset[:-1], 16))
            f.write(b'\x1f\x20\x03\xd5')  # AArch64 NOP

        break


blob_fixups: blob_fixups_user_type = {
    'odm/etc/camera/CameraHWConfiguration.config': blob_fixup()
        .regex_replace('SystemCamera =  0;  0;  1;  1;  1', 'SystemCamera =  0;  0;  0;  0;  1'),
    ('odm/lib/liblvimfs_wrapper.so', 'odm/lib64/libCOppLceTonemapAPI.so', 'odm/lib64/libaps_frame_registration.so', 'vendor/lib64/libalsc.so'): blob_fixup()
        .replace_needed('libstdc++.so', 'libstdc++_vendor.so'),
    ('odm/lib/libdehaze.so', 'odm/lib64/libarcsoft_hdrplus_hvx_stub.so', 'odm/lib64/libarcsoft_high_dynamic_range_v4.so', 'odm/lib64/libarcsoft_portrait_super_night_raw.so', 'odm/lib64/libarcsoft_super_night_raw.so'): blob_fixup()
        .clear_symbol_version('remote_handle_close')
        .clear_symbol_version('remote_handle_invoke')
        .clear_symbol_version('remote_handle_open')
        .clear_symbol_version('remote_handle64_close')
        .clear_symbol_version('remote_handle64_invoke')
        .clear_symbol_version('remote_handle64_open')
        .clear_symbol_version('remote_register_buf_attr')
        .clear_symbol_version('remote_register_buf')
        .clear_symbol_version('rpcmem_alloc')
        .clear_symbol_version('rpcmem_free')
        .clear_symbol_version('rpcmem_to_fd'),
    'odm/lib64/libAlgoProcess.so': blob_fixup()
        .replace_needed('android.hardware.graphics.common-V1-ndk_platform.so', 'android.hardware.graphics.common-V5-ndk.so'),
    'odm/lib64/libOGLManager.so': blob_fixup()
        .clear_symbol_version('AHardwareBuffer_allocate')
        .clear_symbol_version('AHardwareBuffer_describe')
        .clear_symbol_version('AHardwareBuffer_lock')
        .clear_symbol_version('AHardwareBuffer_release')
        .clear_symbol_version('AHardwareBuffer_unlock'),
    'vendor/etc/libnfc-nci.conf': blob_fixup()
        .regex_replace('NFC_DEBUG_ENABLED=1', 'NFC_DEBUG_ENABLED=0'),
    'vendor/etc/libnfc-nxp.conf': blob_fixup()
        .regex_replace('(NXPLOG_.*_LOGLEVEL)=0x03', '\\1=0x02')
        .regex_replace('NFC_DEBUG_ENABLED=1', 'NFC_DEBUG_ENABLED=0'),
    'vendor/lib/hw/audio.primary.lahaina.so': blob_fixup()
        .replace_needed('/vendor/lib/liba2dpoffload.so', '/odm/lib/liba2dpoffload.so')
        .replace_needed('/vendor/lib/libssrec.so', '/odm/lib/libssrec.so')
        .replace_needed('libgui1_vendor.so', 'libgui_vendor.so'),
    'vendor/lib/libextcamera_client.so': blob_fixup()
        .replace_needed('libgui1_vendor.so', 'libgui_vendor.so'),
    'vendor/lib64/vendor.qti.hardware.camera.postproc@1.0-service-impl.so': blob_fixup()
        .call(blob_fixup_nop_call, 'bl', '__cfi_check', '_ZN7android8hardware22configureRpcThreadpoolEmb@plt'),
}  # fmt: skip

module = ExtractUtilsModule(
    'cupidr',
    'realme',
    namespace_imports=namespace_imports,
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    add_firmware_proprietary_file=True,
)

if __name__ == '__main__':
    utils = ExtractUtils.device_with_common(
        module, '../oneplus/sm8350-common', module.vendor
    )
    utils.run()
