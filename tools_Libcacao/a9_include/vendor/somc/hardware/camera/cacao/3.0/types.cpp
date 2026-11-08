#define LOG_TAG "vendor.somc.hardware.camera.cacao@3.0::types"

#include <android/log.h>
#include <cutils/trace.h>
#include <hidl/HidlTransportSupport.h>

#include <vendor/somc/hardware/camera/cacao/3.0/types.h>
#include <vendor/somc/hardware/camera/cacao/3.0/hwtypes.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace cacao {
namespace V3_0 {

::android::status_t readEmbeddedFromParcel(
        const ImageBufInfo &/* obj */,
        const ::android::hardware::Parcel &parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    const native_handle_t *_hidl_imgHandle_ptr;
    _hidl_err = parcel.readNullableEmbeddedNativeHandle(
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::ImageBufInfo, imgHandle),
            &_hidl_imgHandle_ptr
            );

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    return _hidl_err;
}

::android::status_t writeEmbeddedToParcel(
        const ImageBufInfo &obj,
        ::android::hardware::Parcel *parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    _hidl_err = parcel->writeEmbeddedNativeHandle(
            obj.imgHandle,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::ImageBufInfo, imgHandle));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    return _hidl_err;
}

::android::status_t readEmbeddedFromParcel(
        const Param &obj,
        const ::android::hardware::Parcel &parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_string &>(obj.name),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::Param, name));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    const native_handle_t *_hidl_handle0_ptr;
    _hidl_err = parcel.readNullableEmbeddedNativeHandle(
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::Param, handle0),
            &_hidl_handle0_ptr
            );

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    const native_handle_t *_hidl_handle1_ptr;
    _hidl_err = parcel.readNullableEmbeddedNativeHandle(
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::Param, handle1),
            &_hidl_handle1_ptr
            );

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_bufInfos_child;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_vec<::vendor::somc::hardware::camera::cacao::V3_0::ImageBufInfo> &>(obj.bufInfos),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::Param, bufInfos), &_hidl_bufInfos_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    for (size_t _hidl_index_0 = 0; _hidl_index_0 < obj.bufInfos.size(); ++_hidl_index_0) {
        _hidl_err = readEmbeddedFromParcel(
                const_cast<::vendor::somc::hardware::camera::cacao::V3_0::ImageBufInfo &>(obj.bufInfos[_hidl_index_0]),
                parcel,
                _hidl_bufInfos_child,
                _hidl_index_0 * sizeof(::vendor::somc::hardware::camera::cacao::V3_0::ImageBufInfo));

        if (_hidl_err != ::android::OK) { return _hidl_err; }

    }

    return _hidl_err;
}

::android::status_t writeEmbeddedToParcel(
        const Param &obj,
        ::android::hardware::Parcel *parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.name,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::Param, name));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    _hidl_err = parcel->writeEmbeddedNativeHandle(
            obj.handle0,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::Param, handle0));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    _hidl_err = parcel->writeEmbeddedNativeHandle(
            obj.handle1,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::Param, handle1));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_bufInfos_child;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.bufInfos,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::Param, bufInfos), &_hidl_bufInfos_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    for (size_t _hidl_index_0 = 0; _hidl_index_0 < obj.bufInfos.size(); ++_hidl_index_0) {
        _hidl_err = writeEmbeddedToParcel(
                obj.bufInfos[_hidl_index_0],
                parcel,
                _hidl_bufInfos_child,
                _hidl_index_0 * sizeof(::vendor::somc::hardware::camera::cacao::V3_0::ImageBufInfo));

        if (_hidl_err != ::android::OK) { return _hidl_err; }

    }

    return _hidl_err;
}

::android::status_t readEmbeddedFromParcel(
        const SupportedInfo &obj,
        const ::android::hardware::Parcel &parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    size_t _hidl_sizes_child;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_vec<::vendor::somc::hardware::camera::cacao::V3_0::ImageSize> &>(obj.sizes),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::SupportedInfo, sizes), &_hidl_sizes_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_formats_child;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_vec<uint32_t> &>(obj.formats),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::SupportedInfo, formats), &_hidl_formats_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    return _hidl_err;
}

::android::status_t writeEmbeddedToParcel(
        const SupportedInfo &obj,
        ::android::hardware::Parcel *parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    size_t _hidl_sizes_child;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.sizes,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::SupportedInfo, sizes), &_hidl_sizes_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_formats_child;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.formats,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::SupportedInfo, formats), &_hidl_formats_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    return _hidl_err;
}

::android::status_t readEmbeddedFromParcel(
        const SuperSlowCaps &obj,
        const ::android::hardware::Parcel &parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    size_t _hidl_sizes_child;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_vec<::vendor::somc::hardware::camera::cacao::V3_0::ImageSize> &>(obj.sizes),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::SuperSlowCaps, sizes), &_hidl_sizes_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_formats0_child;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_vec<uint32_t> &>(obj.formats0),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::SuperSlowCaps, formats0), &_hidl_formats0_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_formats1_child;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_vec<uint32_t> &>(obj.formats1),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::SuperSlowCaps, formats1), &_hidl_formats1_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    return _hidl_err;
}

::android::status_t writeEmbeddedToParcel(
        const SuperSlowCaps &obj,
        ::android::hardware::Parcel *parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    size_t _hidl_sizes_child;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.sizes,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::SuperSlowCaps, sizes), &_hidl_sizes_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_formats0_child;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.formats0,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::SuperSlowCaps, formats0), &_hidl_formats0_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_formats1_child;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.formats1,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::SuperSlowCaps, formats1), &_hidl_formats1_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    return _hidl_err;
}

::android::status_t readEmbeddedFromParcel(
        const VideoStabilizationCaps &obj,
        const ::android::hardware::Parcel &parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    size_t _hidl_sizes0_child;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_vec<::vendor::somc::hardware::camera::cacao::V3_0::ImageSize> &>(obj.sizes0),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::VideoStabilizationCaps, sizes0), &_hidl_sizes0_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_formats0_child;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_vec<uint32_t> &>(obj.formats0),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::VideoStabilizationCaps, formats0), &_hidl_formats0_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_sizes1_child;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_vec<::vendor::somc::hardware::camera::cacao::V3_0::ImageSize> &>(obj.sizes1),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::VideoStabilizationCaps, sizes1), &_hidl_sizes1_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_formats1_child;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_vec<uint32_t> &>(obj.formats1),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::VideoStabilizationCaps, formats1), &_hidl_formats1_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    return _hidl_err;
}

::android::status_t writeEmbeddedToParcel(
        const VideoStabilizationCaps &obj,
        ::android::hardware::Parcel *parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    size_t _hidl_sizes0_child;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.sizes0,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::VideoStabilizationCaps, sizes0), &_hidl_sizes0_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_formats0_child;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.formats0,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::VideoStabilizationCaps, formats0), &_hidl_formats0_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_sizes1_child;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.sizes1,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::VideoStabilizationCaps, sizes1), &_hidl_sizes1_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_formats1_child;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.formats1,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::VideoStabilizationCaps, formats1), &_hidl_formats1_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    return _hidl_err;
}

::android::status_t readEmbeddedFromParcel(
        const CacaoCaps &obj,
        const ::android::hardware::Parcel &parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    _hidl_err = readEmbeddedFromParcel(
            const_cast<::vendor::somc::hardware::camera::cacao::V3_0::VideoStabilizationCaps &>(obj.videoStabilization),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::CacaoCaps, videoStabilization));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_sizes_child;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_vec<::vendor::somc::hardware::camera::cacao::V3_0::ImageSize> &>(obj.sizes),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::CacaoCaps, sizes), &_hidl_sizes_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_formats_child;

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_vec<uint32_t> &>(obj.formats),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::CacaoCaps, formats), &_hidl_formats_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    _hidl_err = readEmbeddedFromParcel(
            const_cast<::vendor::somc::hardware::camera::cacao::V3_0::SuperSlowCaps &>(obj.superSlow),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::CacaoCaps, superSlow));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    return _hidl_err;
}

::android::status_t writeEmbeddedToParcel(
        const CacaoCaps &obj,
        ::android::hardware::Parcel *parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    _hidl_err = writeEmbeddedToParcel(
            obj.videoStabilization,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::CacaoCaps, videoStabilization));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_sizes_child;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.sizes,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::CacaoCaps, sizes), &_hidl_sizes_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    size_t _hidl_formats_child;

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            obj.formats,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::CacaoCaps, formats), &_hidl_formats_child);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    _hidl_err = writeEmbeddedToParcel(
            obj.superSlow,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_0::CacaoCaps, superSlow));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    return _hidl_err;
}

static_assert(sizeof(::android::hardware::MQDescriptor<char, ::android::hardware::kSynchronizedReadWrite>) == 32, "wrong size");
static_assert(sizeof(::android::hardware::hidl_handle) == 16, "wrong size");
static_assert(sizeof(::android::hardware::hidl_memory) == 40, "wrong size");
static_assert(sizeof(::android::hardware::hidl_string) == 16, "wrong size");
static_assert(sizeof(::android::hardware::hidl_vec<char>) == 16, "wrong size");

}  // namespace V3_0
}  // namespace cacao
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor
