#ifndef HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V3_2_ICAMERADEVICE_H
#define HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V3_2_ICAMERADEVICE_H

#include <android/hardware/camera/common/1.0/types.h>
#include <android/hardware/camera/device/3.2/ICameraDeviceCallback.h>
#include <android/hardware/camera/device/3.2/ICameraDeviceSession.h>
#include <android/hardware/camera/device/3.2/types.h>
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
namespace device {
namespace V3_2 {

struct ICameraDevice : public ::android::hidl::base::V1_0::IBase {
    typedef android::hardware::details::i_tag _hidl_tag;

    // Forward declaration for forward reference support:

    /**
     * Camera device HAL, first modern version
     * 
     * Supports the android.hardware.Camera API, and the android.hardware.camera2
     * API at LIMITED or better hardware level.
     * 
     */
    virtual bool isRemote() const override { return false; }


    using getResourceCost_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, const ::android::hardware::camera::common::V1_0::CameraResourceCost& resourceCost)>;
    /**
     * Get camera device resource cost information.
     * 
     * @return status Status code for the operation, one of:
     *     OK:
     *         On success
     *     INTERNAL_ERROR:
     *         An unexpected internal camera HAL error occurred, and the
     *         resource cost is not available.
     *     CAMERA_DISCONNECTED:
     *         An external camera device has been disconnected, and is no longer
     *         available. This camera device interface is now stale, and a new
     *         instance must be acquired if the device is reconnected. All
     *         subsequent calls on this interface must return
     *         CAMERA_DISCONNECTED.
     * @return resourceCost
     *     The resources required to open this camera device, or unspecified
     *     values if status is not OK.
     */
    virtual ::android::hardware::Return<void> getResourceCost(getResourceCost_cb _hidl_cb) = 0;

    using getCameraCharacteristics_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, const ::android::hardware::hidl_vec<uint8_t>& cameraCharacteristics)>;
    /**
     * getCameraCharacteristics:
     * 
     * Return the static camera information for this camera device. This
     * information may not change between consecutive calls.
     * 
     * When an external camera is disconnected, its camera id becomes
     * invalid. Calling this method with this invalid camera id must result in
     * ILLEGAL_ARGUMENT; this may happen even before the device status callback
     * is invoked by the HAL.
     * 
     * @return status Status code for the operation, one of:
     *     OK:
     *         On a successful open of the camera device.
     *     INTERNAL_ERROR:
     *         The camera device cannot be opened due to an internal
     *         error.
     *     CAMERA_DISCONNECTED:
     *         An external camera device has been disconnected, and is no longer
     *         available. This camera device interface is now stale, and a new
     *         instance must be acquired if the device is reconnected. All
     *         subsequent calls on this interface must return
     *         CAMERA_DISCONNECTED.
     * 
     * @return cameraCharacteristics
     *     The static metadata for this camera device, or an empty metadata
     *     structure if status is not OK.
     * 
     */
    virtual ::android::hardware::Return<void> getCameraCharacteristics(getCameraCharacteristics_cb _hidl_cb) = 0;

    /**
     * setTorchMode:
     * 
     * Turn on or off the torch mode of the flash unit associated with this
     * camera device. If the operation is successful, HAL must notify the
     * framework torch state by invoking
     * ICameraProviderCallback::torchModeStatusChange() with the new state.
     * 
     * An active camera session has a higher priority accessing the flash
     * unit. When there are any resource conflicts, such as when open() is
     * called to fully activate a camera device, the provider must notify the
     * framework through ICameraProviderCallback::torchModeStatusChange() that
     * the torch mode has been turned off and the torch mode state has become
     * TORCH_MODE_STATUS_NOT_AVAILABLE. When resources to turn on torch mode
     * become available again, the provider must notify the framework through
     * ICameraProviderCallback::torchModeStatusChange() that the torch mode
     * state has become TORCH_MODE_STATUS_AVAILABLE_OFF for set_torch_mode() to
     * be called.
     * 
     * When the client calls setTorchMode() to turn on the torch mode of a flash
     * unit, if the HAL cannot keep multiple torch modes on simultaneously, the
     * HAL must turn off the torch mode(s) that were turned on by previous
     * setTorchMode() calls and notify the framework that the torch mode state
     * of those flash unit(s) has become TORCH_MODE_STATUS_AVAILABLE_OFF.
     * 
     * @param torchMode The new mode to set the device flash unit to.
     * 
     * @return status Status code for the operation, one of:
     *     OK:
     *         On a successful change to the torch state
     *     INTERNAL_ERROR:
     *         The flash unit cannot be operated due to an unexpected internal
     *         error.
     *     ILLEGAL_ARGUMENT:
     *         The camera ID is unknown.
     *     CAMERA_IN_USE:
     *         This camera device has been opened, so the torch cannot be
     *         controlled until it is closed.
     *     MAX_CAMERAS_IN_USE:
     *         Due to other camera devices being open, or due to other
     *         resource constraints, the torch cannot be controlled currently.
     *     METHOD_NOT_SUPPORTED:
     *         This provider does not support direct operation of flashlight
     *         torch mode. The framework must open the camera device and turn
     *         the torch on through the device interface.
     *     OPERATION_NOT_SUPPORTED:
     *         This camera device does not have a flash unit. This can
     *         be returned if and only if android.flash.info.available is
     *         false.
     *     CAMERA_DISCONNECTED:
     *         An external camera device has been disconnected, and is no longer
     *         available. This camera device interface is now stale, and a new
     *         instance must be acquired if the device is reconnected. All
     *         subsequent calls on this interface must return
     *         CAMERA_DISCONNECTED.
     * 
     */
    virtual ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> setTorchMode(::android::hardware::camera::common::V1_0::TorchMode mode) = 0;

    using open_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, const ::android::sp<::android::hardware::camera::device::V3_2::ICameraDeviceSession>& session)>;
    /**
     * open:
     * 
     * Power on and initialize this camera device for active use, returning a
     * session handle for active operations.
     * 
     * @param callback Interface to invoke by the HAL for device asynchronous
     *     events. For HALs newer than version 3.2, HAL must use castFrom
     *     method to check the exact version of callback sent by camera service.
     * 
     * @return status Status code for the operation, one of:
     *     OK:
     *         On a successful open of the camera device.
     *     INTERNAL_ERROR:
     *         The camera device cannot be opened due to an internal
     *         error.
     *     ILLEGAL_ARGUMENT:
     *         The callbacks handle is invalid (for example, it is null).
     *     CAMERA_IN_USE:
     *         This camera device is already open.
     *     MAX_CAMERAS_IN_USE:
     *         The maximal number of camera devices that can be
     *         opened concurrently were opened already.
     *     CAMERA_DISCONNECTED:
     *         This external camera device has been disconnected, and is no
     *         longer available. This interface is now stale, and a new instance
     *         must be acquired if the device is reconnected. All subsequent
     *         calls on this interface must return CAMERA_DISCONNECTED.
     * @return session The interface to the newly-opened camera session,
     *     or null if status is not OK.
     */
    virtual ::android::hardware::Return<void> open(const ::android::sp<::android::hardware::camera::device::V3_2::ICameraDeviceCallback>& callback, open_cb _hidl_cb) = 0;

    /**
     * dumpState:
     * 
     * Print out debugging state for the camera device. This may be called by
     * the framework when the camera service is asked for a debug dump, which
     * happens when using the dumpsys tool, or when capturing a bugreport.
     * 
     * The passed-in file descriptor can be used to write debugging text using
     * dprintf() or write(). The text must be in ASCII encoding only.
     * 
     * In case this camera device has been disconnected, the dump must not fail,
     * but may simply print out 'Device disconnected' or equivalent.
     * 
     * Performance requirements:
     * 
     * This must be a non-blocking call. The HAL should return from this call
     * in 1ms, must return from this call in 10ms. This call must avoid
     * deadlocks, as it may be called at any point during camera operation.
     * Any synchronization primitives used (such as mutex locks or semaphores)
     * must be acquired with a timeout.
     */
    virtual ::android::hardware::Return<void> dumpState(const ::android::hardware::hidl_handle& fd) = 0;

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
    static ::android::hardware::Return<::android::sp<::android::hardware::camera::device::V3_2::ICameraDevice>> castFrom(const ::android::sp<::android::hardware::camera::device::V3_2::ICameraDevice>& parent, bool emitError = false);
    static ::android::hardware::Return<::android::sp<::android::hardware::camera::device::V3_2::ICameraDevice>> castFrom(const ::android::sp<::android::hidl::base::V1_0::IBase>& parent, bool emitError = false);

    static const char* descriptor;

    static ::android::sp<ICameraDevice> tryGetService(const std::string &serviceName="default", bool getStub=false);
    static ::android::sp<ICameraDevice> tryGetService(const char serviceName[], bool getStub=false)  { std::string str(serviceName ? serviceName : "");      return tryGetService(str, getStub); }
    static ::android::sp<ICameraDevice> tryGetService(const ::android::hardware::hidl_string& serviceName, bool getStub=false)  { std::string str(serviceName.c_str());      return tryGetService(str, getStub); }
    static ::android::sp<ICameraDevice> tryGetService(bool getStub) { return tryGetService("default", getStub); }
    static ::android::sp<ICameraDevice> getService(const std::string &serviceName="default", bool getStub=false);
    static ::android::sp<ICameraDevice> getService(const char serviceName[], bool getStub=false)  { std::string str(serviceName ? serviceName : "");      return getService(str, getStub); }
    static ::android::sp<ICameraDevice> getService(const ::android::hardware::hidl_string& serviceName, bool getStub=false)  { std::string str(serviceName.c_str());      return getService(str, getStub); }
    static ::android::sp<ICameraDevice> getService(bool getStub) { return getService("default", getStub); }
    __attribute__ ((warn_unused_result))::android::status_t registerAsService(const std::string &serviceName="default");
    static bool registerForNotifications(
            const std::string &serviceName,
            const ::android::sp<::android::hidl::manager::V1_0::IServiceNotification> &notification);
};

static inline std::string toString(const ::android::sp<::android::hardware::camera::device::V3_2::ICameraDevice>& o) {
    std::string os = "[class or subclass of ";
    os += ::android::hardware::camera::device::V3_2::ICameraDevice::descriptor;
    os += "]";
    os += o->isRemote() ? "@remote" : "@local";
    return os;
}


}  // namespace V3_2
}  // namespace device
}  // namespace camera
}  // namespace hardware
}  // namespace android

#endif  // HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V3_2_ICAMERADEVICE_H
