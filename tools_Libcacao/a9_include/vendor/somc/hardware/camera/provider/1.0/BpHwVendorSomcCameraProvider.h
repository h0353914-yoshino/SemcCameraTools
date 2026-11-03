#ifndef HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_PROVIDER_V1_0_BPHWVENDORSOMCCAMERAPROVIDER_H
#define HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_PROVIDER_V1_0_BPHWVENDORSOMCCAMERAPROVIDER_H

#include <hidl/HidlTransportSupport.h>

#include <vendor/somc/hardware/camera/provider/1.0/IHwVendorSomcCameraProvider.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace provider {
namespace V1_0 {

struct BpHwVendorSomcCameraProvider : public ::android::hardware::BpInterface<IVendorSomcCameraProvider>, public ::android::hardware::details::HidlInstrumentor {
    explicit BpHwVendorSomcCameraProvider(const ::android::sp<::android::hardware::IBinder> &_hidl_impl);

    typedef IVendorSomcCameraProvider Pure;

    typedef android::hardware::details::bphw_tag _hidl_tag;

    virtual bool isRemote() const override { return true; }

    // Methods from ::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider follow.
    static ::android::hardware::Return<void>  _hidl_getCameraExtensionDeviceInterface_V1_0(::android::hardware::IInterface* _hidl_this, ::android::hardware::details::HidlInstrumentor *_hidl_this_instrumentor, const ::android::hardware::hidl_string& cameraDeviceName, getCameraExtensionDeviceInterface_V1_0_cb _hidl_cb);
    static ::android::hardware::Return<void>  _hidl_getCacaoInterface_V1_0(::android::hardware::IInterface* _hidl_this, ::android::hardware::details::HidlInstrumentor *_hidl_this_instrumentor, getCacaoInterface_V1_0_cb _hidl_cb);
    static ::android::hardware::Return<void>  _hidl_getCacaoInterface_V2_0(::android::hardware::IInterface* _hidl_this, ::android::hardware::details::HidlInstrumentor *_hidl_this_instrumentor, getCacaoInterface_V2_0_cb _hidl_cb);
    static ::android::hardware::Return<void>  _hidl_getCacaoInterface_V3_0(::android::hardware::IInterface* _hidl_this, ::android::hardware::details::HidlInstrumentor *_hidl_this_instrumentor, getCacaoInterface_V3_0_cb _hidl_cb);

    // Methods from ::android::hardware::camera::provider::V2_4::ICameraProvider follow.
    ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> setCallback(const ::android::sp<::android::hardware::camera::provider::V2_4::ICameraProviderCallback>& callback) override;
    ::android::hardware::Return<void> getVendorTags(getVendorTags_cb _hidl_cb) override;
    ::android::hardware::Return<void> getCameraIdList(getCameraIdList_cb _hidl_cb) override;
    ::android::hardware::Return<void> isSetTorchModeSupported(isSetTorchModeSupported_cb _hidl_cb) override;
    ::android::hardware::Return<void> getCameraDeviceInterface_V1_x(const ::android::hardware::hidl_string& cameraDeviceName, getCameraDeviceInterface_V1_x_cb _hidl_cb) override;
    ::android::hardware::Return<void> getCameraDeviceInterface_V3_x(const ::android::hardware::hidl_string& cameraDeviceName, getCameraDeviceInterface_V3_x_cb _hidl_cb) override;

    // Methods from ::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider follow.
    ::android::hardware::Return<void> getCameraExtensionDeviceInterface_V1_0(const ::android::hardware::hidl_string& cameraDeviceName, getCameraExtensionDeviceInterface_V1_0_cb _hidl_cb) override;
    ::android::hardware::Return<void> getCacaoInterface_V1_0(getCacaoInterface_V1_0_cb _hidl_cb) override;
    ::android::hardware::Return<void> getCacaoInterface_V2_0(getCacaoInterface_V2_0_cb _hidl_cb) override;
    ::android::hardware::Return<void> getCacaoInterface_V3_0(getCacaoInterface_V3_0_cb _hidl_cb) override;

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
}  // namespace provider
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor

#endif  // HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_PROVIDER_V1_0_BPHWVENDORSOMCCAMERAPROVIDER_H
