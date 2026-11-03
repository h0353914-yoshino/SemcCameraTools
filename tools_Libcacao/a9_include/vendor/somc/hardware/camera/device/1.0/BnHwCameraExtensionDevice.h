#ifndef HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_DEVICE_V1_0_BNHWCAMERAEXTENSIONDEVICE_H
#define HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_DEVICE_V1_0_BNHWCAMERAEXTENSIONDEVICE_H

#include <vendor/somc/hardware/camera/device/1.0/IHwCameraExtensionDevice.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace device {
namespace V1_0 {

struct BnHwCameraExtensionDevice : public ::android::hidl::base::V1_0::BnHwBase {
    explicit BnHwCameraExtensionDevice(const ::android::sp<ICameraExtensionDevice> &_hidl_impl);
    explicit BnHwCameraExtensionDevice(const ::android::sp<ICameraExtensionDevice> &_hidl_impl, const std::string& HidlInstrumentor_package, const std::string& HidlInstrumentor_interface);

    virtual ~BnHwCameraExtensionDevice();

    ::android::status_t onTransact(
            uint32_t _hidl_code,
            const ::android::hardware::Parcel &_hidl_data,
            ::android::hardware::Parcel *_hidl_reply,
            uint32_t _hidl_flags = 0,
            TransactCallback _hidl_cb = nullptr) override;


    typedef ICameraExtensionDevice Pure;

    typedef android::hardware::details::bnhw_tag _hidl_tag;

    ::android::sp<ICameraExtensionDevice> getImpl() { return _hidl_mImpl; }

private:
    // Methods from ::android::hidl::base::V1_0::IBase follow.
    ::android::hardware::Return<void> ping();
    using getDebugInfo_cb = ::android::hidl::base::V1_0::IBase::getDebugInfo_cb;
    ::android::hardware::Return<void> getDebugInfo(getDebugInfo_cb _hidl_cb);

    ::android::sp<ICameraExtensionDevice> _hidl_mImpl;
};

}  // namespace V1_0
}  // namespace device
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor

#endif  // HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_DEVICE_V1_0_BNHWCAMERAEXTENSIONDEVICE_H
