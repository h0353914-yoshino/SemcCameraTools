#ifndef HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_DEVICE_V1_0_BPHWCAMERAEXTENSIONDEVICE_H
#define HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_DEVICE_V1_0_BPHWCAMERAEXTENSIONDEVICE_H

#include <hidl/HidlTransportSupport.h>

#include <vendor/somc/hardware/camera/device/1.0/IHwCameraExtensionDevice.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace device {
namespace V1_0 {

struct BpHwCameraExtensionDevice : public ::android::hardware::BpInterface<ICameraExtensionDevice>, public ::android::hardware::details::HidlInstrumentor {
    explicit BpHwCameraExtensionDevice(const ::android::sp<::android::hardware::IBinder> &_hidl_impl);

    typedef ICameraExtensionDevice Pure;

    typedef android::hardware::details::bphw_tag _hidl_tag;

    virtual bool isRemote() const override { return true; }


    // Methods from ::android::hidl::base::V1_0::IBase follow.
    ::android::hardware::Return<void> interfaceChain(interfaceChain_cb _hidl_cb) override;
    ::android::hardware::Return<void> debug(const ::android::hardware::hidl_handle& fd, const ::android::hardware::hidl_vec<::android::hardware::hidl_string>& options) override;
    ::android::hardware::Return<void> interfaceDescriptor(interfaceDescriptor_cb _hidl_cb) override;
    ::android::hardware::Return<void> getHashChain(getHashChain_cb _hidl_cb) override;
    ::android::hardware::Return<void> setHALInstrumentation() override;
    ::android::hardware::Return<bool> linkToDeath(const ::android::sp<::android::hardware::hidl_death_recipient>& recipient, uint64_t cookie) override;
    ::android::hardware::Return<void> ping() override;
    ::android::hardware::Return<void> getDebugInfo(getDebugInfo_cb _hidl_cb) override;
    ::android::hardware::Return<void> notifySyspropsChanged() override;
    ::android::hardware::Return<bool> unlinkToDeath(const ::android::sp<::android::hardware::hidl_death_recipient>& recipient) override;

private:
    std::mutex _hidl_mMutex;
    std::vector<::android::sp<::android::hardware::hidl_binder_death_recipient>> _hidl_mDeathRecipients;
};

}  // namespace V1_0
}  // namespace device
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor

#endif  // HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_DEVICE_V1_0_BPHWCAMERAEXTENSIONDEVICE_H
