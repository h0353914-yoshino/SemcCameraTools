#ifndef HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V1_0_ICAMERADEVICEPREVIEWCALLBACK_H
#define HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V1_0_ICAMERADEVICEPREVIEWCALLBACK_H

#include <android/hardware/camera/common/1.0/types.h>
#include <android/hardware/graphics/common/1.0/types.h>
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

struct ICameraDevicePreviewCallback : public ::android::hidl::base::V1_0::IBase {
    typedef android::hardware::details::i_tag _hidl_tag;

    // Forward declaration for forward reference support:

    /**
     * Camera device HAL@1.0 preview stream operation interface.
     */
    virtual bool isRemote() const override { return false; }


    using dequeueBuffer_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, uint64_t bufferId, const ::android::hardware::hidl_handle& buffer, uint32_t stride)>;
    /**
     * Acquire a buffer to write a preview buffer into.
     * 
     * @return status The status code for this operation. If not OK, then
     *     buffer and stride must not be used.
     * @return bufferId A unique ID for the returned buffer.
     * @return buffer A handle to the buffer to write into. Must be non-null if the bufferId has not
     *     been seen by HAL before. Must be null if the bufferId is seen before. HAL must keep track
     *     of the bufferId to actual buffer handle mapping.
     * @return stride The stride between two rows of pixels in this buffer.
     */
    virtual ::android::hardware::Return<void> dequeueBuffer(dequeueBuffer_cb _hidl_cb) = 0;

    /**
     * Send a filled preview buffer to its consumer.
     * 
     * @param bufferId The bufferId of the preview buffer
     * @return status The status code for this operation.
     */
    virtual ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> enqueueBuffer(uint64_t bufferId) = 0;

    /**
     * Return a preview buffer unfilled. This buffer must not be sent on to the
     * preview consumer as a valid buffer, but may be reused as if it were
     * empty.
     * 
     * @param bufferId The bufferId of the preview buffer
     * @return status The status code for this operation.
     */
    virtual ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> cancelBuffer(uint64_t bufferId) = 0;

    /**
     * Set the number of preview buffers needed by the HAL.
     * 
     * @param count The maximum number of preview buffers to allocate.
     * @return status The status code for this operation.
     */
    virtual ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> setBufferCount(uint32_t count) = 0;

    /**
     * Set the dimensions and format of future preview buffers.
     * 
     * The next buffer that is dequeued must match the requested size and
     * format.
     * 
     * @return Status The status code for this operation.
     */
    virtual ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> setBuffersGeometry(uint32_t w, uint32_t h, ::android::hardware::graphics::common::V1_0::PixelFormat format) = 0;

    /**
     * Set the valid region of image data for the next buffer(s) to be enqueued.
     * 
     * @return Status The status code for this operation.
     */
    virtual ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> setCrop(int32_t left, int32_t top, int32_t right, int32_t bottom) = 0;

    /**
     * Set the producer usage flags for the next buffer(s) to be enqueued.
     * 
     * @return Status The status code for this operation.
     */
    virtual ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> setUsage(::android::hardware::graphics::common::V1_0::BufferUsage usage) = 0;

    /**
     * Set the expected buffering mode for the preview output.
     */
    virtual ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> setSwapInterval(int32_t interval) = 0;

    using getMinUndequeuedBufferCount_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, uint32_t count)>;
    /**
     * Get the minimum number of buffers the preview consumer endpoint needs
     * to hold for correct operation.
     * 
     * @return Status The status code for this operation.
     * @return count The number of buffers the consumer has requested.
     */
    virtual ::android::hardware::Return<void> getMinUndequeuedBufferCount(getMinUndequeuedBufferCount_cb _hidl_cb) = 0;

    /**
     * Set the timestamp for the next buffer to enqueue
     * 
     * Timestamps are measured in nanoseconds, and must be comparable
     * and monotonically increasing between two frames in the same
     * preview stream. They do not need to be comparable between
     * consecutive or parallel preview streams, cameras, or app runs.
     * 
     * @param timestamp The timestamp to set for future buffers.
     * @return Status The status code for this operation.
     */
    virtual ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> setTimestamp(int64_t timestamp) = 0;

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
    static ::android::hardware::Return<::android::sp<::android::hardware::camera::device::V1_0::ICameraDevicePreviewCallback>> castFrom(const ::android::sp<::android::hardware::camera::device::V1_0::ICameraDevicePreviewCallback>& parent, bool emitError = false);
    static ::android::hardware::Return<::android::sp<::android::hardware::camera::device::V1_0::ICameraDevicePreviewCallback>> castFrom(const ::android::sp<::android::hidl::base::V1_0::IBase>& parent, bool emitError = false);

    static const char* descriptor;

    static ::android::sp<ICameraDevicePreviewCallback> tryGetService(const std::string &serviceName="default", bool getStub=false);
    static ::android::sp<ICameraDevicePreviewCallback> tryGetService(const char serviceName[], bool getStub=false)  { std::string str(serviceName ? serviceName : "");      return tryGetService(str, getStub); }
    static ::android::sp<ICameraDevicePreviewCallback> tryGetService(const ::android::hardware::hidl_string& serviceName, bool getStub=false)  { std::string str(serviceName.c_str());      return tryGetService(str, getStub); }
    static ::android::sp<ICameraDevicePreviewCallback> tryGetService(bool getStub) { return tryGetService("default", getStub); }
    static ::android::sp<ICameraDevicePreviewCallback> getService(const std::string &serviceName="default", bool getStub=false);
    static ::android::sp<ICameraDevicePreviewCallback> getService(const char serviceName[], bool getStub=false)  { std::string str(serviceName ? serviceName : "");      return getService(str, getStub); }
    static ::android::sp<ICameraDevicePreviewCallback> getService(const ::android::hardware::hidl_string& serviceName, bool getStub=false)  { std::string str(serviceName.c_str());      return getService(str, getStub); }
    static ::android::sp<ICameraDevicePreviewCallback> getService(bool getStub) { return getService("default", getStub); }
    __attribute__ ((warn_unused_result))::android::status_t registerAsService(const std::string &serviceName="default");
    static bool registerForNotifications(
            const std::string &serviceName,
            const ::android::sp<::android::hidl::manager::V1_0::IServiceNotification> &notification);
};

static inline std::string toString(const ::android::sp<::android::hardware::camera::device::V1_0::ICameraDevicePreviewCallback>& o) {
    std::string os = "[class or subclass of ";
    os += ::android::hardware::camera::device::V1_0::ICameraDevicePreviewCallback::descriptor;
    os += "]";
    os += o->isRemote() ? "@remote" : "@local";
    return os;
}


}  // namespace V1_0
}  // namespace device
}  // namespace camera
}  // namespace hardware
}  // namespace android

#endif  // HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V1_0_ICAMERADEVICEPREVIEWCALLBACK_H
