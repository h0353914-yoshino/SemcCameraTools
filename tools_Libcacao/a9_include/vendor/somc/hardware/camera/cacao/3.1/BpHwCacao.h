#ifndef HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_1_BPHWCACAO_H
#define HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_1_BPHWCACAO_H

#include <hidl/HidlTransportSupport.h>

#include <vendor/somc/hardware/camera/cacao/3.1/IHwCacao.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace cacao {
namespace V3_1 {

struct BpHwCacao : public ::android::hardware::BpInterface<ICacao>, public ::android::hardware::details::HidlInstrumentor {
    explicit BpHwCacao(const ::android::sp<::android::hardware::IBinder> &_hidl_impl);

    typedef ICacao Pure;

    typedef android::hardware::details::bphw_tag _hidl_tag;

    virtual bool isRemote() const override { return true; }

    // Methods from ::vendor::somc::hardware::camera::cacao::V3_1::ICacao follow.
    static ::android::hardware::Return<void>  _hidl_getCapsV3_1(::android::hardware::IInterface* _hidl_this, ::android::hardware::details::HidlInstrumentor *_hidl_this_instrumentor, ::vendor::somc::hardware::camera::cacao::V3_0::CameraIndex camIdx, getCapsV3_1_cb _hidl_cb);

    // Methods from ::vendor::somc::hardware::camera::cacao::V3_0::ICacao follow.
    ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> setCallback(const ::android::sp<::vendor::somc::hardware::camera::cacao::V3_0::ICacaoCallback>& callback) override;
    ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> start(const ::vendor::somc::hardware::camera::cacao::V3_0::ControlMode& mode) override;
    ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> stop() override;
    ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> setConfig(const ::vendor::somc::hardware::camera::cacao::V3_0::Config& config) override;
    ::android::hardware::Return<void> getConfig(::vendor::somc::hardware::camera::cacao::V3_0::ConfigId configId, getConfig_cb _hidl_cb) override;
    ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> process(const ::vendor::somc::hardware::camera::cacao::V3_0::Param& param) override;
    ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> processAsync(const ::vendor::somc::hardware::camera::cacao::V3_0::Param& param, const ::vendor::somc::hardware::camera::cacao::V3_0::Result& result) override;
    ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> setColorSpaceForHandle(const ::android::hardware::hidl_handle& bufHandle, ::vendor::somc::hardware::camera::cacao::V3_0::DataSpace dataSpace) override;
    ::android::hardware::Return<void> getCaps(::vendor::somc::hardware::camera::cacao::V3_0::CameraIndex camIdx, getCaps_cb _hidl_cb) override;
    ::android::hardware::Return<void> getJpegBufferSize(const ::vendor::somc::hardware::camera::cacao::V3_0::ImageSize& size, getJpegBufferSize_cb _hidl_cb) override;

    // Methods from ::vendor::somc::hardware::camera::cacao::V3_1::ICacao follow.
    ::android::hardware::Return<void> getCapsV3_1(::vendor::somc::hardware::camera::cacao::V3_0::CameraIndex camIdx, getCapsV3_1_cb _hidl_cb) override;

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

}  // namespace V3_1
}  // namespace cacao
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor

#endif  // HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_1_BPHWCACAO_H
