#ifndef HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_0_ICACAO_H
#define HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_0_ICACAO_H

#include <android/hidl/base/1.0/IBase.h>
#include <vendor/somc/hardware/camera/cacao/3.0/ICacaoCallback.h>
#include <vendor/somc/hardware/camera/cacao/3.0/types.h>

#include <android/hidl/manager/1.0/IServiceNotification.h>

#include <hidl/HidlSupport.h>
#include <hidl/MQDescriptor.h>
#include <hidl/Status.h>
#include <utils/NativeHandle.h>
#include <utils/misc.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace cacao {
namespace V3_0 {

struct ICacao : public ::android::hidl::base::V1_0::IBase {
    typedef android::hardware::details::i_tag _hidl_tag;

    // Forward declaration for forward reference support:

    virtual bool isRemote() const override { return false; }


    virtual ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> setCallback(const ::android::sp<::vendor::somc::hardware::camera::cacao::V3_0::ICacaoCallback>& callback) = 0;

    virtual ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> start(const ::vendor::somc::hardware::camera::cacao::V3_0::ControlMode& mode) = 0;

    virtual ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> stop() = 0;

    virtual ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> setConfig(const ::vendor::somc::hardware::camera::cacao::V3_0::Config& config) = 0;

    using getConfig_cb = std::function<void(const ::vendor::somc::hardware::camera::cacao::V3_0::Config& config, ::vendor::somc::hardware::camera::cacao::V3_0::ErrCode err)>;
    virtual ::android::hardware::Return<void> getConfig(::vendor::somc::hardware::camera::cacao::V3_0::ConfigId configId, getConfig_cb _hidl_cb) = 0;

    virtual ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> process(const ::vendor::somc::hardware::camera::cacao::V3_0::Param& param) = 0;

    virtual ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> processAsync(const ::vendor::somc::hardware::camera::cacao::V3_0::Param& param, const ::vendor::somc::hardware::camera::cacao::V3_0::Result& result) = 0;

    virtual ::android::hardware::Return<::vendor::somc::hardware::camera::cacao::V3_0::ErrCode> setColorSpaceForHandle(const ::android::hardware::hidl_handle& bufHandle, ::vendor::somc::hardware::camera::cacao::V3_0::DataSpace dataSpace) = 0;

    using getCaps_cb = std::function<void(const ::vendor::somc::hardware::camera::cacao::V3_0::CacaoCaps& caps, ::vendor::somc::hardware::camera::cacao::V3_0::ErrCode err)>;
    virtual ::android::hardware::Return<void> getCaps(::vendor::somc::hardware::camera::cacao::V3_0::CameraIndex camIdx, getCaps_cb _hidl_cb) = 0;

    using getJpegBufferSize_cb = std::function<void(uint32_t jpegSize, ::vendor::somc::hardware::camera::cacao::V3_0::ErrCode err)>;
    virtual ::android::hardware::Return<void> getJpegBufferSize(const ::vendor::somc::hardware::camera::cacao::V3_0::ImageSize& size, getJpegBufferSize_cb _hidl_cb) = 0;

    using interfaceChain_cb = std::function<void(const ::android::hardware::hidl_vec<::android::hardware::hidl_string>& descriptors)>;
    virtual ::android::hardware::Return<void> interfaceChain(interfaceChain_cb _hidl_cb) override;

    virtual ::android::hardware::Return<void> debug(const ::android::hardware::hidl_handle& fd, const ::android::hardware::hidl_vec<::android::hardware::hidl_string>& options) override;

    using interfaceDescriptor_cb = std::function<void(const ::android::hardware::hidl_string& descriptor)>;
    virtual ::android::hardware::Return<void> interfaceDescriptor(interfaceDescriptor_cb _hidl_cb) override;

    using getHashChain_cb = std::function<void(const ::android::hardware::hidl_vec<::android::hardware::hidl_array<uint8_t, 32>>& hashchain)>;
    virtual ::android::hardware::Return<void> getHashChain(getHashChain_cb _hidl_cb) override;

    virtual ::android::hardware::Return<void> setHALInstrumentation() override;

    virtual ::android::hardware::Return<bool> linkToDeath(const ::android::sp<::android::hardware::hidl_death_recipient>& recipient, uint64_t cookie) override;

    virtual ::android::hardware::Return<void> ping() override;

    using getDebugInfo_cb = std::function<void(const ::android::hidl::base::V1_0::DebugInfo& info)>;
    virtual ::android::hardware::Return<void> getDebugInfo(getDebugInfo_cb _hidl_cb) override;

    virtual ::android::hardware::Return<void> notifySyspropsChanged() override;

    virtual ::android::hardware::Return<bool> unlinkToDeath(const ::android::sp<::android::hardware::hidl_death_recipient>& recipient) override;
    // cast static functions
    static ::android::hardware::Return<::android::sp<::vendor::somc::hardware::camera::cacao::V3_0::ICacao>> castFrom(const ::android::sp<::vendor::somc::hardware::camera::cacao::V3_0::ICacao>& parent, bool emitError = false);
    static ::android::hardware::Return<::android::sp<::vendor::somc::hardware::camera::cacao::V3_0::ICacao>> castFrom(const ::android::sp<::android::hidl::base::V1_0::IBase>& parent, bool emitError = false);

    static const char* descriptor;

    static ::android::sp<ICacao> tryGetService(const std::string &serviceName="default", bool getStub=false);
    static ::android::sp<ICacao> tryGetService(const char serviceName[], bool getStub=false)  { std::string str(serviceName ? serviceName : "");      return tryGetService(str, getStub); }
    static ::android::sp<ICacao> tryGetService(const ::android::hardware::hidl_string& serviceName, bool getStub=false)  { std::string str(serviceName.c_str());      return tryGetService(str, getStub); }
    static ::android::sp<ICacao> tryGetService(bool getStub) { return tryGetService("default", getStub); }
    static ::android::sp<ICacao> getService(const std::string &serviceName="default", bool getStub=false);
    static ::android::sp<ICacao> getService(const char serviceName[], bool getStub=false)  { std::string str(serviceName ? serviceName : "");      return getService(str, getStub); }
    static ::android::sp<ICacao> getService(const ::android::hardware::hidl_string& serviceName, bool getStub=false)  { std::string str(serviceName.c_str());      return getService(str, getStub); }
    static ::android::sp<ICacao> getService(bool getStub) { return getService("default", getStub); }
    __attribute__ ((warn_unused_result))::android::status_t registerAsService(const std::string &serviceName="default");
    static bool registerForNotifications(
            const std::string &serviceName,
            const ::android::sp<::android::hidl::manager::V1_0::IServiceNotification> &notification);
};

static inline std::string toString(const ::android::sp<::vendor::somc::hardware::camera::cacao::V3_0::ICacao>& o) {
    std::string os = "[class or subclass of ";
    os += ::vendor::somc::hardware::camera::cacao::V3_0::ICacao::descriptor;
    os += "]";
    os += o->isRemote() ? "@remote" : "@local";
    return os;
}


}  // namespace V3_0
}  // namespace cacao
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor

#endif  // HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V3_0_ICACAO_H
