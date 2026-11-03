#ifndef HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_0_BPHWCACAOCALLBACK_H
#define HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_0_BPHWCACAOCALLBACK_H

#include <hidl/HidlTransportSupport.h>

#include <vendor/somc/hardware/camera/cacao/3.0/IHwCacaoCallback.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace cacao {
namespace V3_0 {

struct BpHwCacaoCallback : public ::android::hardware::BpInterface<ICacaoCallback>, public ::android::hardware::details::HidlInstrumentor {
    explicit BpHwCacaoCallback(const ::android::sp<::android::hardware::IBinder> &_hidl_impl);

    typedef ICacaoCallback Pure;

    typedef android::hardware::details::bphw_tag _hidl_tag;

    virtual bool isRemote() const override { return true; }

    // Methods from ::vendor::somc::hardware::camera::cacao::V3_0::ICacaoCallback follow.
    static ::android::hardware::Return<void>  _hidl_handleEvent(::android::hardware::IInterface* _hidl_this, ::android::hardware::details::HidlInstrumentor *_hidl_this_instrumentor, const ::vendor::somc::hardware::camera::cacao::V3_0::Event& ev);
    static ::android::hardware::Return<void>  _hidl_handleProgress(::android::hardware::IInterface* _hidl_this, ::android::hardware::details::HidlInstrumentor *_hidl_this_instrumentor, const ::vendor::somc::hardware::camera::cacao::V3_0::Result& res);
    static ::android::hardware::Return<void>  _hidl_handleResult(::android::hardware::IInterface* _hidl_this, ::android::hardware::details::HidlInstrumentor *_hidl_this_instrumentor, const ::vendor::somc::hardware::camera::cacao::V3_0::Result& res);

    // Methods from ::vendor::somc::hardware::camera::cacao::V3_0::ICacaoCallback follow.
    ::android::hardware::Return<void> handleEvent(const ::vendor::somc::hardware::camera::cacao::V3_0::Event& ev) override;
    ::android::hardware::Return<void> handleProgress(const ::vendor::somc::hardware::camera::cacao::V3_0::Result& res) override;
    ::android::hardware::Return<void> handleResult(const ::vendor::somc::hardware::camera::cacao::V3_0::Result& res) override;

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

}  // namespace V3_0
}  // namespace cacao
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor

#endif  // HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_0_BPHWCACAOCALLBACK_H
