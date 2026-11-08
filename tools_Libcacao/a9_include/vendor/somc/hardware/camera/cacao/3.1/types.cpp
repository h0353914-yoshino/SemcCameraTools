#define LOG_TAG "vendor.somc.hardware.camera.cacao@3.1::types"

#include <android/log.h>
#include <cutils/trace.h>
#include <hidl/HidlTransportSupport.h>

#include <vendor/somc/hardware/camera/cacao/3.1/types.h>
#include <vendor/somc/hardware/camera/cacao/3.1/hwtypes.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace cacao {
namespace V3_1 {

::android::status_t readEmbeddedFromParcel(
        const CacaoCaps &obj,
        const ::android::hardware::Parcel &parcel,
        size_t parentHandle,
        size_t parentOffset) {
    ::android::status_t _hidl_err = ::android::OK;

    _hidl_err = readEmbeddedFromParcel(
            const_cast<::vendor::somc::hardware::camera::cacao::V3_0::CacaoCaps &>(obj.base),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps, base));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    _hidl_err = readEmbeddedFromParcel(
            const_cast<::vendor::somc::hardware::camera::cacao::V3_0::SupportedInfo &>(obj.ext0),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps, ext0));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    _hidl_err = readEmbeddedFromParcel(
            const_cast<::vendor::somc::hardware::camera::cacao::V3_0::SupportedInfo &>(obj.ext1),
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps, ext1));

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
            obj.base,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps, base));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    _hidl_err = writeEmbeddedToParcel(
            obj.ext0,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps, ext0));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    _hidl_err = writeEmbeddedToParcel(
            obj.ext1,
            parcel,
            parentHandle,
            parentOffset + offsetof(::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps, ext1));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    return _hidl_err;
}

static_assert(sizeof(::android::hardware::MQDescriptor<char, ::android::hardware::kSynchronizedReadWrite>) == 32, "wrong size");
static_assert(sizeof(::android::hardware::hidl_handle) == 16, "wrong size");
static_assert(sizeof(::android::hardware::hidl_memory) == 40, "wrong size");
static_assert(sizeof(::android::hardware::hidl_string) == 16, "wrong size");
static_assert(sizeof(::android::hardware::hidl_vec<char>) == 16, "wrong size");

}  // namespace V3_1
}  // namespace cacao
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor
