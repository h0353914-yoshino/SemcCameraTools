#ifndef HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V3_2_ICAMERADEVICECALLBACK_H
#define HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V3_2_ICAMERADEVICECALLBACK_H

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

struct ICameraDeviceCallback : public ::android::hidl::base::V1_0::IBase {
    typedef android::hardware::details::i_tag _hidl_tag;

    // Forward declaration for forward reference support:

    /**
     * Callback methods for the HAL to call into the framework.
     * 
     * These methods are used to return metadata and image buffers for a completed
     * or failed captures, and to notify the framework of asynchronous events such
     * as errors.
     * 
     * The framework must not call back into the HAL from within these callbacks,
     * and these calls must not block for extended periods.
     * 
     */
    virtual bool isRemote() const override { return false; }


    /**
     * processCaptureResult:
     * 
     * Send results from one or more completed or partially completed captures
     * to the framework.
     * processCaptureResult() may be invoked multiple times by the HAL in
     * response to a single capture request. This allows, for example, the
     * metadata and low-resolution buffers to be returned in one call, and
     * post-processed JPEG buffers in a later call, once it is available. Each
     * call must include the frame number of the request it is returning
     * metadata or buffers for. Only one call to processCaptureResult
     * may be made at a time by the HAL although the calls may come from
     * different threads in the HAL.
     * 
     * A component (buffer or metadata) of the complete result may only be
     * included in one process_capture_result call. A buffer for each stream,
     * and the result metadata, must be returned by the HAL for each request in
     * one of the processCaptureResult calls, even in case of errors producing
     * some of the output. A call to processCaptureResult() with neither
     * output buffers or result metadata is not allowed.
     * 
     * The order of returning metadata and buffers for a single result does not
     * matter, but buffers for a given stream must be returned in FIFO order. So
     * the buffer for request 5 for stream A must always be returned before the
     * buffer for request 6 for stream A. This also applies to the result
     * metadata; the metadata for request 5 must be returned before the metadata
     * for request 6.
     * 
     * However, different streams are independent of each other, so it is
     * acceptable and expected that the buffer for request 5 for stream A may be
     * returned after the buffer for request 6 for stream B is. And it is
     * acceptable that the result metadata for request 6 for stream B is
     * returned before the buffer for request 5 for stream A is. If multiple
     * capture results are included in a single call, camera framework must
     * process results sequentially from lower index to higher index, as if
     * these results were sent to camera framework one by one, from lower index
     * to higher index.
     * 
     * The HAL retains ownership of result structure, which only needs to be
     * valid to access during this call.
     * 
     * The output buffers do not need to be filled yet; the framework must wait
     * on the stream buffer release sync fence before reading the buffer
     * data. Therefore, this method should be called by the HAL as soon as
     * possible, even if some or all of the output buffers are still in
     * being filled. The HAL must include valid release sync fences into each
     * output_buffers stream buffer entry, or -1 if that stream buffer is
     * already filled.
     * 
     * If the result buffer cannot be constructed for a request, the HAL must
     * return an empty metadata buffer, but still provide the output buffers and
     * their sync fences. In addition, notify() must be called with an
     * ERROR_RESULT message.
     * 
     * If an output buffer cannot be filled, its status field must be set to
     * STATUS_ERROR. In this case, notify() isn't required to be called with
     * an ERROR_BUFFER message. The framework will simply treat the notify()
     * call with ERROR_BUFFER as a no-op, and derive whether and when to notify
     * the application of buffer loss based on the buffer status and whether or not
     * the entire capture has failed.
     * 
     * If the entire capture has failed, then this method still needs to be
     * called to return the output buffers to the framework. All the buffer
     * statuses must be STATUS_ERROR, and the result metadata must be an
     * empty buffer. In addition, notify() must be called with a ERROR_REQUEST
     * message. In this case, individual ERROR_RESULT/ERROR_BUFFER messages
     * must not be sent. Note that valid partial results are still allowed
     * as long as the final result metadata fails to be generated.
     * 
     * Performance requirements:
     * 
     * This is a non-blocking call. The framework must handle each CaptureResult
     * within 5ms.
     * 
     * The pipeline latency (see S7 for definition) should be less than or equal to
     * 4 frame intervals, and must be less than or equal to 8 frame intervals.
     * 
     */
    virtual ::android::hardware::Return<void> processCaptureResult(const ::android::hardware::hidl_vec<::android::hardware::camera::device::V3_2::CaptureResult>& results) = 0;

    /**
     * notify:
     * 
     * Asynchronous notification callback from the HAL, fired for various
     * reasons. Only for information independent of frame capture, or that
     * require specific timing. Multiple messages may be sent in one call; a
     * message with a higher index must be considered to have occurred after a
     * message with a lower index.
     * 
     * Multiple threads may call notify() simultaneously.
     * 
     * Buffers delivered to the framework must not be dispatched to the
     * application layer until a start of exposure timestamp (or input image's
     * start of exposure timestamp for a reprocess request) has been received
     * via a SHUTTER notify() call. It is highly recommended to dispatch this
     * call as early as possible.
     * 
     * The SHUTTER notify calls for requests with android.control.enableZsl
     * set to TRUE and ANDROID_CONTROL_CAPTURE_INTENT == STILL_CAPTURE may be
     * out-of-order compared to SHUTTER notify for other kinds of requests
     * (including regular, reprocess, or zero-shutter-lag requests with
     * different capture intents).
     * 
     * As a result, the capture results of zero-shutter-lag requests with
     * ANDROID_CONTROL_CAPTURE_INTENT == STILL_CAPTURE may be out-of-order
     * compared to capture results for other kinds of requests.
     * 
     * Different SHUTTER notify calls for zero-shutter-lag requests with
     * ANDROID_CONTROL_CAPTURE_INTENT == STILL_CAPTURE must be in order between
     * them, as is for other kinds of requests. SHUTTER notify calls for
     * zero-shutter-lag requests with non STILL_CAPTURE intent must be in order
     * with SHUTTER notify calls for regular requests.
     * ------------------------------------------------------------------------
     * Performance requirements:
     * 
     * This is a non-blocking call. The framework must handle each message in 5ms.
     */
    virtual ::android::hardware::Return<void> notify(const ::android::hardware::hidl_vec<::android::hardware::camera::device::V3_2::NotifyMsg>& msgs) = 0;

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
    static ::android::hardware::Return<::android::sp<::android::hardware::camera::device::V3_2::ICameraDeviceCallback>> castFrom(const ::android::sp<::android::hardware::camera::device::V3_2::ICameraDeviceCallback>& parent, bool emitError = false);
    static ::android::hardware::Return<::android::sp<::android::hardware::camera::device::V3_2::ICameraDeviceCallback>> castFrom(const ::android::sp<::android::hidl::base::V1_0::IBase>& parent, bool emitError = false);

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

static inline std::string toString(const ::android::sp<::android::hardware::camera::device::V3_2::ICameraDeviceCallback>& o) {
    std::string os = "[class or subclass of ";
    os += ::android::hardware::camera::device::V3_2::ICameraDeviceCallback::descriptor;
    os += "]";
    os += o->isRemote() ? "@remote" : "@local";
    return os;
}


}  // namespace V3_2
}  // namespace device
}  // namespace camera
}  // namespace hardware
}  // namespace android

#endif  // HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V3_2_ICAMERADEVICECALLBACK_H
