#ifndef HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_1_TYPES_H
#define HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_1_TYPES_H

#include <vendor/somc/hardware/camera/cacao/3.0/types.h>

#include <hidl/HidlSupport.h>
#include <hidl/MQDescriptor.h>
#include <utils/NativeHandle.h>
#include <utils/misc.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace cacao {
namespace V3_1 {

// Forward declaration for forward reference support:
struct CacaoCaps;

struct CacaoCaps final {
    ::vendor::somc::hardware::camera::cacao::V3_0::CacaoCaps base __attribute__ ((aligned(8)));
    ::android::hardware::hidl_array<uint32_t, 2> reserved0 __attribute__ ((aligned(4)));
    ::vendor::somc::hardware::camera::cacao::V3_0::SupportedInfo ext0 __attribute__ ((aligned(8)));
    ::vendor::somc::hardware::camera::cacao::V3_0::SupportedInfo ext1 __attribute__ ((aligned(8)));
};

static_assert(offsetof(::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps, base) == 0, "wrong offset");
static_assert(offsetof(::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps, reserved0) == 200, "wrong offset");
static_assert(offsetof(::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps, ext0) == 208, "wrong offset");
static_assert(offsetof(::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps, ext1) == 248, "wrong offset");
static_assert(sizeof(::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps) == 288, "wrong size");
static_assert(__alignof(::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps) == 8, "wrong alignment");

static inline std::string toString(const ::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".base = ";
    os += ::vendor::somc::hardware::camera::cacao::V3_0::toString(o.base);
    os += ", .reserved0 = ";
    os += ::android::hardware::toString(o.reserved0);
    os += ", .ext0 = ";
    os += ::vendor::somc::hardware::camera::cacao::V3_0::toString(o.ext0);
    os += ", .ext1 = ";
    os += ::vendor::somc::hardware::camera::cacao::V3_0::toString(o.ext1);
    os += "}"; return os;
}

static inline bool operator==(const ::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps& lhs, const ::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps& rhs) {
    if (lhs.base != rhs.base) {
        return false;
    }
    if (lhs.reserved0 != rhs.reserved0) {
        return false;
    }
    if (lhs.ext0 != rhs.ext0) {
        return false;
    }
    if (lhs.ext1 != rhs.ext1) {
        return false;
    }
    return true;
}

static inline bool operator!=(const ::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps& lhs,const ::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps& rhs){
    return !(lhs == rhs);
}


}  // namespace V3_1
}  // namespace cacao
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor

#endif  // HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_1_TYPES_H
