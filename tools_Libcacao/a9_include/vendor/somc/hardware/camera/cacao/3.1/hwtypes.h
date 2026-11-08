#ifndef HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_1_HWTYPES_H
#define HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_1_HWTYPES_H

#include <vendor/somc/hardware/camera/cacao/3.1/types.h>

#include <vendor/somc/hardware/camera/cacao/3.0/hwtypes.h>

#include <hidl/Status.h>
#include <hwbinder/IBinder.h>
#include <hwbinder/Parcel.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace cacao {
namespace V3_1 {
::android::status_t readEmbeddedFromParcel(
        const ::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps &obj,
        const ::android::hardware::Parcel &parcel,
        size_t parentHandle,
        size_t parentOffset);

::android::status_t writeEmbeddedToParcel(
        const ::vendor::somc::hardware::camera::cacao::V3_1::CacaoCaps &obj,
        ::android::hardware::Parcel *parcel,
        size_t parentHandle,
        size_t parentOffset);

}  // namespace V3_1
}  // namespace cacao
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor

#endif  // HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_1_HWTYPES_H
