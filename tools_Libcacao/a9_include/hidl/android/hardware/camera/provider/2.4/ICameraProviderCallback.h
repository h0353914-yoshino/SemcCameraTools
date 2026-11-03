#ifndef HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_PROVIDER_V2_4_ICAMERAPROVIDERCALLBACK_H
#define HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_PROVIDER_V2_4_ICAMERAPROVIDERCALLBACK_H

#include <android/hardware/camera/common/1.0/types.h>
#include <android/hidl/base/1.0/IBase.h>

#include <android/hidl/manager/1.0/IServiceNotification.h>

#include <hidl/HidlSupport.h>
#include <hidl/MQDescriptor.h>
#include <hidl/Status.h>
#include <utils/NativeHandle.h>
#include <utils/misc.h>

namespace android {
namespace hardware {
namespace camera {
namespace provider {
namespace V2_4 {

struct ICameraProviderCallback : public ::android::hidl::base::V1_0::IBase {
    typedef android::hardware::details::i_tag _hidl_tag;

    // Forward declaration for forward reference support:

    /**
     * Callback functions for a camera provider HAL to use to inform the camera
     * service of changes to the camera subsystem.
     */
    virtual bool isRemote() const override { return false; }


    /**
     * cameraDeviceStatusChange:
     * 
     * Callback to the camera service to indicate that the state of a specific
     * camera device has changed.
     * 
     * On camera service startup, when ICameraProvider::setCallback is invoked,
     * the camera service must assume that all internal camera devices are in
     * the CAMERA_DEVICE_STATUS_PRESENT state.
     * 
     * The provider must call this method to inform the camera service of any
     * initially NOT_PRESENT devices, and of any external camera devices that
     * are already present, as soon as the callbacks are available through
     * setCallback.
     * 
     * @param cameraDeviceName The name of the camera device that has a
     *     new status.
     * @param newStatus The new status that device is in.
     * 
     */
    virtual ::android::hardware::Return<void> cameraDeviceStatusChange(const ::android::hardware::hidl_string& cameraDeviceName, ::android::hardware::camera::common::V1_0::CameraDeviceStatus newStatus) = 0;

    /**
     * torchModeStatusChange:
     * 
     * Callback to the camera service to indicate that the state of the torch
     * mode of the flash unit associated with a specific camera device has
     * changed. At provider registration time, the camera service must assume
     * the torch modes are in the TORCH_MODE_STATUS_AVAILABLE_OFF state if
     * android.flash.info.available is reported as true via the
     * ICameraDevice::getCameraCharacteristics call.
     * 
     * @param cameraDeviceName The name of the camera device that has a
     *     new status.
     * @param newStatus The new status that device is in.
     * 
     */
    virtual ::android::hardware::Return<void> torchModeStatusChange(const ::android::hardware::hidl_string& cameraDeviceName, ::android::hardware::camera::common::V1_0::TorchModeStatus newStatus) = 0;

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
    static ::android::hardware::Return<::android::sp<::android::hardware::camera::provider::V2_4::ICameraProviderCallback>> castFrom(const ::android::sp<::android::hardware::camera::provider::V2_4::ICameraProviderCallback>& parent, bool emitError = false);
    static ::android::hardware::Return<::android::sp<::android::hardware::camera::provider::V2_4::ICameraProviderCallback>> castFrom(const ::android::sp<::android::hidl::base::V1_0::IBase>& parent, bool emitError = false);

    static const char* descriptor;

    static ::android::sp<ICameraProviderCallback> tryGetService(const std::string &serviceName="default", bool getStub=false);
    static ::android::sp<ICameraProviderCallback> tryGetService(const char serviceName[], bool getStub=false)  { std::string str(serviceName ? serviceName : "");      return tryGetService(str, getStub); }
    static ::android::sp<ICameraProviderCallback> tryGetService(const ::android::hardware::hidl_string& serviceName, bool getStub=false)  { std::string str(serviceName.c_str());      return tryGetService(str, getStub); }
    static ::android::sp<ICameraProviderCallback> tryGetService(bool getStub) { return tryGetService("default", getStub); }
    static ::android::sp<ICameraProviderCallback> getService(const std::string &serviceName="default", bool getStub=false);
    static ::android::sp<ICameraProviderCallback> getService(const char serviceName[], bool getStub=false)  { std::string str(serviceName ? serviceName : "");      return getService(str, getStub); }
    static ::android::sp<ICameraProviderCallback> getService(const ::android::hardware::hidl_string& serviceName, bool getStub=false)  { std::string str(serviceName.c_str());      return getService(str, getStub); }
    static ::android::sp<ICameraProviderCallback> getService(bool getStub) { return getService("default", getStub); }
    __attribute__ ((warn_unused_result))::android::status_t registerAsService(const std::string &serviceName="default");
    static bool registerForNotifications(
            const std::string &serviceName,
            const ::android::sp<::android::hidl::manager::V1_0::IServiceNotification> &notification);
};

static inline std::string toString(const ::android::sp<::android::hardware::camera::provider::V2_4::ICameraProviderCallback>& o) {
    std::string os = "[class or subclass of ";
    os += ::android::hardware::camera::provider::V2_4::ICameraProviderCallback::descriptor;
    os += "]";
    os += o->isRemote() ? "@remote" : "@local";
    return os;
}


}  // namespace V2_4
}  // namespace provider
}  // namespace camera
}  // namespace hardware
}  // namespace android

#endif  // HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_PROVIDER_V2_4_ICAMERAPROVIDERCALLBACK_H
