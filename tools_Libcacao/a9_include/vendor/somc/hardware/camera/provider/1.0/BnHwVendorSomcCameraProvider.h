#ifndef HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_PROVIDER_V1_0_BNHWVENDORSOMCCAMERAPROVIDER_H
#define HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_PROVIDER_V1_0_BNHWVENDORSOMCCAMERAPROVIDER_H

#include <vendor/somc/hardware/camera/provider/1.0/IHwVendorSomcCameraProvider.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace provider {
namespace V1_0 {

struct BnHwVendorSomcCameraProvider : public ::android::hidl::base::V1_0::BnHwBase {
    explicit BnHwVendorSomcCameraProvider(const ::android::sp<IVendorSomcCameraProvider> &_hidl_impl);
    explicit BnHwVendorSomcCameraProvider(const ::android::sp<IVendorSomcCameraProvider> &_hidl_impl, const std::string& HidlInstrumentor_package, const std::string& HidlInstrumentor_interface);

    virtual ~BnHwVendorSomcCameraProvider();

    ::android::status_t onTransact(
            uint32_t _hidl_code,
            const ::android::hardware::Parcel &_hidl_data,
            ::android::hardware::Parcel *_hidl_reply,
            uint32_t _hidl_flags = 0,
            TransactCallback _hidl_cb = nullptr) override;


    typedef IVendorSomcCameraProvider Pure;

    typedef android::hardware::details::bnhw_tag _hidl_tag;

    ::android::sp<IVendorSomcCameraProvider> getImpl() { return _hidl_mImpl; }
    // Methods from ::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider follow.
    static ::android::status_t _hidl_getCameraExtensionDeviceInterface_V1_0(
            ::android::hidl::base::V1_0::BnHwBase* _hidl_this,
            const ::android::hardware::Parcel &_hidl_data,
            ::android::hardware::Parcel *_hidl_reply,
            TransactCallback _hidl_cb);


    static ::android::status_t _hidl_getCacaoInterface_V1_0(
            ::android::hidl::base::V1_0::BnHwBase* _hidl_this,
            const ::android::hardware::Parcel &_hidl_data,
            ::android::hardware::Parcel *_hidl_reply,
            TransactCallback _hidl_cb);


    static ::android::status_t _hidl_getCacaoInterface_V2_0(
            ::android::hidl::base::V1_0::BnHwBase* _hidl_this,
            const ::android::hardware::Parcel &_hidl_data,
            ::android::hardware::Parcel *_hidl_reply,
            TransactCallback _hidl_cb);


    static ::android::status_t _hidl_getCacaoInterface_V3_0(
            ::android::hidl::base::V1_0::BnHwBase* _hidl_this,
            const ::android::hardware::Parcel &_hidl_data,
            ::android::hardware::Parcel *_hidl_reply,
            TransactCallback _hidl_cb);



private:
    // Methods from ::android::hardware::camera::provider::V2_4::ICameraProvider follow.

    // Methods from ::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider follow.

    // Methods from ::android::hidl::base::V1_0::IBase follow.
    ::android::hardware::Return<void> ping();
    using getDebugInfo_cb = ::android::hidl::base::V1_0::IBase::getDebugInfo_cb;
    ::android::hardware::Return<void> getDebugInfo(getDebugInfo_cb _hidl_cb);

    ::android::sp<IVendorSomcCameraProvider> _hidl_mImpl;
};

}  // namespace V1_0
}  // namespace provider
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor

#endif  // HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_PROVIDER_V1_0_BNHWVENDORSOMCCAMERAPROVIDER_H
