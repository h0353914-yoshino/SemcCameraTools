#ifndef HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V1_0_ICAMERADEVICECALLBACK_H
#define HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V1_0_ICAMERADEVICECALLBACK_H

#include <android/hardware/camera/device/1.0/types.h>
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
namespace V1_0 {

struct ICameraDeviceCallback : public ::android::hidl::base::V1_0::IBase {
    typedef android::hardware::details::i_tag _hidl_tag;

    // Forward declaration for forward reference support:

    virtual bool isRemote() const override { return false; }


    /**
     * Notify the camera service of a particular event occurring
     * The meaning of each parameter is defined by the value of msgType, and
     * documented in the definition of NotifyCallbackMsg.
     * 
     * @param msgType The type of the event.
     * @param ext1 The first parameter for the event, if needed.
     * @param ext2 The second parameter for the event, if needed.
     */
    virtual ::android::hardware::Return<void> notifyCallback(::android::hardware::camera::device::V1_0::NotifyCallbackMsg msgType, int32_t ext1, int32_t ext2) = 0;

    /**
     * Define a memory buffer from the provided handle and size, and return a
     * unique identifier for the HAL to use to reference it with.
     * 
     * @param descriptor A native handle that must have exactly one file
     *     descriptor in it; the file descriptor must be memory mappable to
     *     bufferSize * bufferCount bytes.
     * @param bufferSize The number of bytes a single buffer consists of.
     * @param bufferCount The number of contiguous buffers that the descriptor
     *     contains.
     * 
     * @return memId A positive integer identifier for this memory buffer, for
     *     use with data callbacks and unregistering memory. 0 must be returned
     *     in case of error, such as if the descriptor does not contain exactly
     *     one FD.
     */
    virtual ::android::hardware::Return<uint32_t> registerMemory(const ::android::hardware::hidl_handle& descriptor, uint32_t bufferSize, uint32_t bufferCount) = 0;

    /**
     * Unregister a previously registered memory buffer
     */
    virtual ::android::hardware::Return<void> unregisterMemory(uint32_t memId) = 0;

    /**
     * Send a buffer of image data to the camera service
     * 
     * @param msgType The kind of image buffer data this call represents.
     * @param data A memory handle to the buffer containing the data.
     * @param bufferIndex The offset into the memory handle where the buffer
     *     starts.
     * 
     */
    virtual ::android::hardware::Return<void> dataCallback(::android::hardware::camera::device::V1_0::DataCallbackMsg msgType, uint32_t data, uint32_t bufferIndex, const ::android::hardware::camera::device::V1_0::CameraFrameMetadata& metadata) = 0;

    /**
     * Send a buffer of image data to the camera service, with a timestamp
     * 
     * @param msgType The kind of image buffer data this call represents.
     * @param data A memory handle to the buffer containing the data.
     * @param bufferIndex The offset into the memory handle where the buffer
     *     starts.
     * @param timestamp The time this buffer was captured by the camera, in
     *     nanoseconds.
     * 
     */
    virtual ::android::hardware::Return<void> dataCallbackTimestamp(::android::hardware::camera::device::V1_0::DataCallbackMsg msgType, uint32_t data, uint32_t bufferIndex, int64_t timestamp) = 0;

    /**
     * Send a buffer of image data to the camera service, with a timestamp
     * 
     * @param msgType The kind of image buffer data this call represents.
     * @param handle The handle of image buffer data this call represents.
     * @param data A memory handle to the buffer containing the data.
     * @param bufferIndex The offset into the memory handle where the buffer
     *     starts.
     * @param timestamp The time this buffer was captured by the camera, in
     *     nanoseconds.
     * 
     */
    virtual ::android::hardware::Return<void> handleCallbackTimestamp(::android::hardware::camera::device::V1_0::DataCallbackMsg msgType, const ::android::hardware::hidl_handle& frameData, uint32_t data, uint32_t bufferIndex, int64_t timestamp) = 0;

    /**
     * Send a batch of image data buffer to the camera service, with timestamps
     * 
     * This callback can be used to send multiple frames to camera framework in one callback, which
     * reduce number of callbacks in performance intensive use cases, such as high speed video
     * recording. The HAL must not mix use of this method with handleCallbackTimestamp in one
     * recording session (between startRecording and stopRecording)
     * 
     * @param msgType The kind of image buffer data this call represents.
     * @param batch a vector messages. Each message contains a image buffer and a timestamp. The
     *     messages must be ordered in time from lower index to higher index, so that timestamp of
     *     i-th message is always smaller than i+1-th message.
     * 
     */
    virtual ::android::hardware::Return<void> handleCallbackTimestampBatch(::android::hardware::camera::device::V1_0::DataCallbackMsg msgType, const ::android::hardware::hidl_vec<::android::hardware::camera::device::V1_0::HandleTimestampMessage>& batch) = 0;

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
    static ::android::hardware::Return<::android::sp<::android::hardware::camera::device::V1_0::ICameraDeviceCallback>> castFrom(const ::android::sp<::android::hardware::camera::device::V1_0::ICameraDeviceCallback>& parent, bool emitError = false);
    static ::android::hardware::Return<::android::sp<::android::hardware::camera::device::V1_0::ICameraDeviceCallback>> castFrom(const ::android::sp<::android::hidl::base::V1_0::IBase>& parent, bool emitError = false);

    static const char* descriptor;

    static ::android::sp<ICameraDeviceCallback> tryGetService(const std::string &serviceName="default", bool getStub=false);
    static ::android::sp<ICameraDeviceCallback> tryGetService(const char serviceName[], bool getStub=false)  { std::string str(serviceName ? serviceName : "");      return tryGetService(str, getStub); }
    static ::android::sp<ICameraDeviceCallback> tryGetService(const ::android::hardware::hidl_string& serviceName, bool getStub=false)  { std::string str(serviceName.c_str());      return tryGetService(str, getStub); }
    static ::android::sp<ICameraDeviceCallback> tryGetService(bool getStub) { return tryGetService("default", getStub); }
    static ::android::sp<ICameraDeviceCallback> getService(const std::string &serviceName="default", bool getStub=false);
    static ::android::sp<ICameraDeviceCallback> getService(const char serviceName[], bool getStub=false)  { std::string str(serviceName ? serviceName : "");      return getService(str, getStub); }
    static ::android::sp<ICameraDeviceCallback> getService(const ::android::hardware::hidl_string& serviceName, bool getStub=false)  { std::string str(serviceName.c_str());      return getService(str, getStub); }
    static ::android::sp<ICameraDeviceCallback> getService(bool getStub) { return getService("default", getStub); }
    __attribute__ ((warn_unused_result))::android::status_t registerAsService(const std::string &serviceName="default");
    static bool registerForNotifications(
            const std::string &serviceName,
            const ::android::sp<::android::hidl::manager::V1_0::IServiceNotification> &notification);
};

static inline std::string toString(const ::android::sp<::android::hardware::camera::device::V1_0::ICameraDeviceCallback>& o) {
    std::string os = "[class or subclass of ";
    os += ::android::hardware::camera::device::V1_0::ICameraDeviceCallback::descriptor;
    os += "]";
    os += o->isRemote() ? "@remote" : "@local";
    return os;
}


}  // namespace V1_0
}  // namespace device
}  // namespace camera
}  // namespace hardware
}  // namespace android

#endif  // HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V1_0_ICAMERADEVICECALLBACK_H
