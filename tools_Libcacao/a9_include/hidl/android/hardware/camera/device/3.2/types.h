#ifndef HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V3_2_TYPES_H
#define HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V3_2_TYPES_H

#include <android/hardware/graphics/common/1.0/types.h>

#include <hidl/HidlSupport.h>
#include <hidl/MQDescriptor.h>
#include <utils/NativeHandle.h>
#include <utils/misc.h>

namespace android {
namespace hardware {
namespace camera {
namespace device {
namespace V3_2 {

// Forward declaration for forward reference support:
enum class StreamType : uint32_t;
enum class StreamRotation : uint32_t;
enum class StreamConfigurationMode : uint32_t;
struct Stream;
struct StreamConfiguration;
struct HalStream;
struct HalStreamConfiguration;
enum class BufferStatus : uint32_t;
struct StreamBuffer;
enum class CameraBlobId : uint16_t;
struct CameraBlob;
enum class MsgType : uint32_t;
enum class ErrorCode : uint32_t;
struct ErrorMsg;
struct ShutterMsg;
struct NotifyMsg;
enum class RequestTemplate : uint32_t;
struct CaptureRequest;
struct CaptureResult;
struct BufferCache;

typedef ::android::hardware::hidl_vec<uint8_t> CameraMetadata;

typedef ::android::hardware::hidl_bitfield<::android::hardware::graphics::common::V1_0::BufferUsage> BufferUsageFlags;

typedef ::android::hardware::hidl_bitfield<::android::hardware::graphics::common::V1_0::Dataspace> DataspaceFlags;

/**
 * StreamType:
 * 
 * The type of the camera stream, which defines whether the camera HAL device is
 * the producer or the consumer for that stream, and how the buffers of the
 * stream relate to the other streams.
 */
enum class StreamType : uint32_t {
    /**
     * This stream is an output stream; the camera HAL device must fill buffers
     * from this stream with newly captured or reprocessed image data.
     */
    OUTPUT = 0u,
    /**
     * This stream is an input stream; the camera HAL device must read buffers
     * from this stream and send them through the camera processing pipeline,
     * as if the buffer was a newly captured image from the imager.
     * 
     * The pixel format for input stream can be any format reported by
     * android.scaler.availableInputOutputFormatsMap. The pixel format of the
     * output stream that is used to produce the reprocessing data may be any
     * format reported by android.scaler.availableStreamConfigurations. The
     * supported input/output stream combinations depends the camera device
     * capabilities, see android.scaler.availableInputOutputFormatsMap for
     * stream map details.
     * 
     * This kind of stream is generally used to reprocess data into higher
     * quality images (that otherwise would cause a frame rate performance
     * loss), or to do off-line reprocessing.
     * 
     * The typical use cases are OPAQUE (typically ZSL) and YUV reprocessing,
     * see S8.2, S8.3 and S10 for more details.
     */
    INPUT = 1u,
};

/**
 * StreamRotation:
 * 
 * The required counterclockwise rotation of camera stream.
 */
enum class StreamRotation : uint32_t {
    /**
     * No rotation  */
    ROTATION_0 = 0u,
    /**
     * Rotate by 90 degree counterclockwise  */
    ROTATION_90 = 1u,
    /**
     * Rotate by 180 degree counterclockwise  */
    ROTATION_180 = 2u,
    /**
     * Rotate by 270 degree counterclockwise  */
    ROTATION_270 = 3u,
};

/**
 * StreamConfigurationMode:
 * 
 * This defines the general operation mode for the HAL (for a given stream
 * configuration) where modes besides NORMAL have different semantics, and
 * usually limit the generality of the API in exchange for higher performance in
 * some particular area.
 */
enum class StreamConfigurationMode : uint32_t {
    /**
     * Normal stream configuration operation mode. This is the default camera
     * operation mode, where all semantics of HAL APIs and metadata controls
     * apply.
     */
    NORMAL_MODE = 0u,
    /**
     * Special constrained high speed operation mode for devices that can not
     * support high speed output in NORMAL mode. All streams in this
     * configuration are operating at high speed mode and have different
     * characteristics and limitations to achieve high speed output. The NORMAL
     * mode can still be used for high speed output if the HAL can support high
     * speed output while satisfying all the semantics of HAL APIs and metadata
     * controls. It is recommended for the HAL to support high speed output in
     * NORMAL mode (by advertising the high speed FPS ranges in
     * android.control.aeAvailableTargetFpsRanges) if possible.
     * 
     * This mode has below limitations/requirements:
     * 
     *   1. The HAL must support up to 2 streams with sizes reported by
     *      android.control.availableHighSpeedVideoConfigurations.
     *   2. In this mode, the HAL is expected to output up to 120fps or
     *      higher. This mode must support the targeted FPS range and size
     *      configurations reported by
     *      android.control.availableHighSpeedVideoConfigurations.
     *   3. The HAL must support IMPLEMENTATION_DEFINED output
     *      stream format.
     *   4. To achieve efficient high speed streaming, the HAL may have to
     *      aggregate multiple frames together and send to camera device for
     *      processing where the request controls are same for all the frames in
     *      this batch (batch mode). The HAL must support max batch size and the
     *      max batch size requirements defined by
     *      android.control.availableHighSpeedVideoConfigurations.
     *   5. In this mode, the HAL must override aeMode, awbMode, and afMode to
     *      ON, ON, and CONTINUOUS_VIDEO, respectively. All post-processing
     *      block mode controls must be overridden to be FAST. Therefore, no
     *      manual control of capture and post-processing parameters is
     *      possible. All other controls operate the same as when
     *      android.control.mode == AUTO. This means that all other
     *      android.control.* fields must continue to work, such as
     * 
     *      android.control.aeTargetFpsRange
     *      android.control.aeExposureCompensation
     *      android.control.aeLock
     *      android.control.awbLock
     *      android.control.effectMode
     *      android.control.aeRegions
     *      android.control.afRegions
     *      android.control.awbRegions
     *      android.control.afTrigger
     *      android.control.aePrecaptureTrigger
     * 
     *      Outside of android.control.*, the following controls must work:
     * 
     *      android.flash.mode (TORCH mode only, automatic flash for still
     *          capture must not work since aeMode is ON)
     *      android.lens.opticalStabilizationMode (if it is supported)
     *      android.scaler.cropRegion
     *      android.statistics.faceDetectMode (if it is supported)
     *   6. To reduce the amount of data passed across process boundaries at
     *      high frame rate, within one batch, camera framework only propagates
     *      the last shutter notify and the last capture results (including partial
     *      results and final result) to the app. The shutter notifies and capture
     *      results for the other requests in the batch are derived by
     *      the camera framework. As a result, the HAL can return empty metadata
     *      except for the last result in the batch.
     * 
     * For more details about high speed stream requirements, see
     * android.control.availableHighSpeedVideoConfigurations and
     * CONSTRAINED_HIGH_SPEED_VIDEO capability defined in
     * android.request.availableCapabilities.
     * 
     * This mode only needs to be supported by HALs that include
     * CONSTRAINED_HIGH_SPEED_VIDEO in the android.request.availableCapabilities
     * static metadata.
     */
    CONSTRAINED_HIGH_SPEED_MODE = 1u,
    /**
     * A set of vendor-defined operating modes, for custom default camera
     * application features that can't be implemented in the fully flexible fashion
     * required for NORMAL_MODE.
     */
    VENDOR_MODE_0 = 32768u,
    VENDOR_MODE_1 = 32769u, // (::android::hardware::camera::device::V3_2::StreamConfigurationMode.VENDOR_MODE_0 implicitly + 1)
    VENDOR_MODE_2 = 32770u, // (::android::hardware::camera::device::V3_2::StreamConfigurationMode.VENDOR_MODE_1 implicitly + 1)
    VENDOR_MODE_3 = 32771u, // (::android::hardware::camera::device::V3_2::StreamConfigurationMode.VENDOR_MODE_2 implicitly + 1)
    VENDOR_MODE_4 = 32772u, // (::android::hardware::camera::device::V3_2::StreamConfigurationMode.VENDOR_MODE_3 implicitly + 1)
    VENDOR_MODE_5 = 32773u, // (::android::hardware::camera::device::V3_2::StreamConfigurationMode.VENDOR_MODE_4 implicitly + 1)
    VENDOR_MODE_6 = 32774u, // (::android::hardware::camera::device::V3_2::StreamConfigurationMode.VENDOR_MODE_5 implicitly + 1)
    VENDOR_MODE_7 = 32775u, // (::android::hardware::camera::device::V3_2::StreamConfigurationMode.VENDOR_MODE_6 implicitly + 1)
};

/**
 * Stream:
 * 
 * A descriptor for a single camera input or output stream. A stream is defined
 * by the framework by its buffer resolution and format, and additionally by the
 * HAL with the gralloc usage flags and the maximum in-flight buffer count.
 * 
 * If a configureStreams() call returns a non-fatal error, all active streams
 * remain valid as if configureStreams() had not been called.
 * 
 */
struct Stream final {
    int32_t id __attribute__ ((aligned(4)));
    ::android::hardware::camera::device::V3_2::StreamType streamType __attribute__ ((aligned(4)));
    uint32_t width __attribute__ ((aligned(4)));
    uint32_t height __attribute__ ((aligned(4)));
    ::android::hardware::graphics::common::V1_0::PixelFormat format __attribute__ ((aligned(4)));
    ::android::hardware::hidl_bitfield<::android::hardware::graphics::common::V1_0::BufferUsage> usage __attribute__ ((aligned(8)));
    ::android::hardware::hidl_bitfield<::android::hardware::graphics::common::V1_0::Dataspace> dataSpace __attribute__ ((aligned(4)));
    ::android::hardware::camera::device::V3_2::StreamRotation rotation __attribute__ ((aligned(4)));
};

static_assert(offsetof(::android::hardware::camera::device::V3_2::Stream, id) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::Stream, streamType) == 4, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::Stream, width) == 8, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::Stream, height) == 12, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::Stream, format) == 16, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::Stream, usage) == 24, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::Stream, dataSpace) == 32, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::Stream, rotation) == 36, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V3_2::Stream) == 40, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V3_2::Stream) == 8, "wrong alignment");

/**
 * StreamConfiguration:
 * 
 * A structure of stream definitions, used by configureStreams(). This
 * structure defines all the output streams and the reprocessing input
 * stream for the current camera use case.
 */
struct StreamConfiguration final {
    ::android::hardware::hidl_vec<::android::hardware::camera::device::V3_2::Stream> streams __attribute__ ((aligned(8)));
    ::android::hardware::camera::device::V3_2::StreamConfigurationMode operationMode __attribute__ ((aligned(4)));
};

static_assert(offsetof(::android::hardware::camera::device::V3_2::StreamConfiguration, streams) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::StreamConfiguration, operationMode) == 16, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V3_2::StreamConfiguration) == 24, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V3_2::StreamConfiguration) == 8, "wrong alignment");

/**
 * HalStream:
 * 
 * The camera HAL's response to each requested stream configuration.
 * 
 * The HAL may specify the desired format, maximum buffers, and
 * usage flags for each stream.
 * 
 */
struct HalStream final {
    int32_t id __attribute__ ((aligned(4)));
    ::android::hardware::graphics::common::V1_0::PixelFormat overrideFormat __attribute__ ((aligned(4)));
    ::android::hardware::hidl_bitfield<::android::hardware::graphics::common::V1_0::BufferUsage> producerUsage __attribute__ ((aligned(8)));
    ::android::hardware::hidl_bitfield<::android::hardware::graphics::common::V1_0::BufferUsage> consumerUsage __attribute__ ((aligned(8)));
    uint32_t maxBuffers __attribute__ ((aligned(4)));
};

static_assert(offsetof(::android::hardware::camera::device::V3_2::HalStream, id) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::HalStream, overrideFormat) == 4, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::HalStream, producerUsage) == 8, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::HalStream, consumerUsage) == 16, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::HalStream, maxBuffers) == 24, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V3_2::HalStream) == 32, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V3_2::HalStream) == 8, "wrong alignment");

/**
 * HalStreamConfiguration:
 * 
 * A structure of stream definitions, returned by configureStreams(). This
 * structure defines the HAL's desired parameters for each stream.
 * 
 * All streams that were defined in the input to configureStreams() must have a
 * corresponding entry in this structure when returned by configureStreams().
 */
struct HalStreamConfiguration final {
    ::android::hardware::hidl_vec<::android::hardware::camera::device::V3_2::HalStream> streams __attribute__ ((aligned(8)));
};

static_assert(offsetof(::android::hardware::camera::device::V3_2::HalStreamConfiguration, streams) == 0, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V3_2::HalStreamConfiguration) == 16, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V3_2::HalStreamConfiguration) == 8, "wrong alignment");

/**
 * BufferStatus:
 * 
 * The current status of a single stream buffer.
 */
enum class BufferStatus : uint32_t {
    /**
     * The buffer is in a normal state, and can be used after waiting on its
     * sync fence.
     */
    OK = 0u,
    /**
     * The buffer does not contain valid data, and the data in it must not be
     * used. The sync fence must still be waited on before reusing the buffer.
     */
    ERROR = 1u,
};

/**
 * StreamBuffer:
 * 
 * A single buffer from a camera3 stream. It includes a handle to its parent
 * stream, the handle to the gralloc buffer itself, and sync fences
 * 
 * The buffer does not specify whether it is to be used for input or output;
 * that is determined by its parent stream type and how the buffer is passed to
 * the HAL device.
 */
struct StreamBuffer final {
    int32_t streamId __attribute__ ((aligned(4)));
    uint64_t bufferId __attribute__ ((aligned(8)));
    ::android::hardware::hidl_handle buffer __attribute__ ((aligned(8)));
    ::android::hardware::camera::device::V3_2::BufferStatus status __attribute__ ((aligned(4)));
    ::android::hardware::hidl_handle acquireFence __attribute__ ((aligned(8)));
    ::android::hardware::hidl_handle releaseFence __attribute__ ((aligned(8)));
};

static_assert(offsetof(::android::hardware::camera::device::V3_2::StreamBuffer, streamId) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::StreamBuffer, bufferId) == 8, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::StreamBuffer, buffer) == 16, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::StreamBuffer, status) == 32, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::StreamBuffer, acquireFence) == 40, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::StreamBuffer, releaseFence) == 56, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V3_2::StreamBuffer) == 72, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V3_2::StreamBuffer) == 8, "wrong alignment");

/**
 * CameraBlob:
 * 
 * Transport header for camera blob types; generally compressed JPEG buffers in
 * output streams.
 * 
 * To capture JPEG images, a stream is created using the pixel format
 * HAL_PIXEL_FORMAT_BLOB and dataspace HAL_DATASPACE_V0_JFIF. The buffer size
 * for the stream is calculated by the framework, based on the static metadata
 * field android.jpeg.maxSize. Since compressed JPEG images are of variable
 * size, the HAL needs to include the final size of the compressed image using
 * this structure inside the output stream buffer. The camera blob ID field must
 * be set to CameraBlobId::JPEG.
 * 
 * The transport header must be at the end of the JPEG output stream
 * buffer. That means the jpegBlobId must start at byte[buffer_size -
 * sizeof(CameraBlob)], where the buffer_size is the size of gralloc
 * buffer. Any HAL using this transport header must account for it in
 * android.jpeg.maxSize. The JPEG data itself starts at the beginning of the
 * buffer and must be blobSize bytes long.
 */
enum class CameraBlobId : uint16_t {
    JPEG = 255,
};

struct CameraBlob final {
    ::android::hardware::camera::device::V3_2::CameraBlobId blobId __attribute__ ((aligned(2)));
    uint32_t blobSize __attribute__ ((aligned(4)));
};

static_assert(offsetof(::android::hardware::camera::device::V3_2::CameraBlob, blobId) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::CameraBlob, blobSize) == 4, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V3_2::CameraBlob) == 8, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V3_2::CameraBlob) == 4, "wrong alignment");

/**
 * MsgType:
 * 
 * Indicates the type of message sent, which specifies which member of the
 * message union is valid.
 * 
 */
enum class MsgType : uint32_t {
    /**
     * An error has occurred. NotifyMsg::Message::Error contains the
     * error information.
     */
    ERROR = 1u,
    /**
     * The exposure of a given request or processing a reprocess request has
     * begun. NotifyMsg::Message::Shutter contains the information
     * the capture.
     */
    SHUTTER = 2u,
};

/**
 * Defined error codes for MsgType::ERROR
 */
enum class ErrorCode : uint32_t {
    /**
     * A serious failure occured. No further frames or buffer streams must
     * be produced by the device. Device must be treated as closed. The
     * client must reopen the device to use it again. The frameNumber field
     * is unused.
     */
    ERROR_DEVICE = 1u,
    /**
     * An error has occurred in processing a request. No output (metadata or
     * buffers) must be produced for this request. The frameNumber field
     * specifies which request has been dropped. Subsequent requests are
     * unaffected, and the device remains operational.
     */
    ERROR_REQUEST = 2u,
    /**
     * An error has occurred in producing an output result metadata buffer
     * for a request, but output stream buffers for it must still be
     * available. Subsequent requests are unaffected, and the device remains
     * operational. The frameNumber field specifies the request for which
     * result metadata won't be available.
     */
    ERROR_RESULT = 3u,
    /**
     * An error has occurred in placing an output buffer into a stream for a
     * request. The frame metadata and other buffers may still be
     * available. Subsequent requests are unaffected, and the device remains
     * operational. The frameNumber field specifies the request for which the
     * buffer was dropped, and errorStreamId indicates the stream
     * that dropped the frame.
     */
    ERROR_BUFFER = 4u,
};

/**
 * ErrorMsg:
 * 
 * Message contents for MsgType::ERROR
 */
struct ErrorMsg final {
    uint32_t frameNumber __attribute__ ((aligned(4)));
    int32_t errorStreamId __attribute__ ((aligned(4)));
    ::android::hardware::camera::device::V3_2::ErrorCode errorCode __attribute__ ((aligned(4)));
};

static_assert(offsetof(::android::hardware::camera::device::V3_2::ErrorMsg, frameNumber) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::ErrorMsg, errorStreamId) == 4, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::ErrorMsg, errorCode) == 8, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V3_2::ErrorMsg) == 12, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V3_2::ErrorMsg) == 4, "wrong alignment");

/**
 * ShutterMsg:
 * 
 * Message contents for MsgType::SHUTTER
 */
struct ShutterMsg final {
    uint32_t frameNumber __attribute__ ((aligned(4)));
    uint64_t timestamp __attribute__ ((aligned(8)));
};

static_assert(offsetof(::android::hardware::camera::device::V3_2::ShutterMsg, frameNumber) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::ShutterMsg, timestamp) == 8, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V3_2::ShutterMsg) == 16, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V3_2::ShutterMsg) == 8, "wrong alignment");

/**
 * NotifyMsg:
 * 
 * The message structure sent to ICameraDevice3Callback::notify()
 */
struct NotifyMsg final {
    // Forward declaration for forward reference support:
    union Message;

    union Message final {
        ::android::hardware::camera::device::V3_2::ErrorMsg error __attribute__ ((aligned(4)));
        ::android::hardware::camera::device::V3_2::ShutterMsg shutter __attribute__ ((aligned(8)));
    };

    static_assert(offsetof(::android::hardware::camera::device::V3_2::NotifyMsg::Message, error) == 0, "wrong offset");
    static_assert(offsetof(::android::hardware::camera::device::V3_2::NotifyMsg::Message, shutter) == 0, "wrong offset");
    static_assert(sizeof(::android::hardware::camera::device::V3_2::NotifyMsg::Message) == 16, "wrong size");
    static_assert(__alignof(::android::hardware::camera::device::V3_2::NotifyMsg::Message) == 8, "wrong alignment");

    ::android::hardware::camera::device::V3_2::MsgType type __attribute__ ((aligned(4)));
    ::android::hardware::camera::device::V3_2::NotifyMsg::Message msg __attribute__ ((aligned(8)));
};

static_assert(offsetof(::android::hardware::camera::device::V3_2::NotifyMsg, type) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::NotifyMsg, msg) == 8, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V3_2::NotifyMsg) == 24, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V3_2::NotifyMsg) == 8, "wrong alignment");

/**
 * RequestTemplate:
 * 
 * Available template types for
 * ICameraDevice::constructDefaultRequestSettings()
 */
enum class RequestTemplate : uint32_t {
    /**
     * Standard camera preview operation with 3A on auto.
     */
    PREVIEW = 1u,
    /**
     * Standard camera high-quality still capture with 3A and flash on auto.
     */
    STILL_CAPTURE = 2u,
    /**
     * Standard video recording plus preview with 3A on auto, torch off.
     */
    VIDEO_RECORD = 3u,
    /**
     * High-quality still capture while recording video. Applications typically
     * include preview, video record, and full-resolution YUV or JPEG streams in
     * request. Must not cause stuttering on video stream. 3A on auto.
     */
    VIDEO_SNAPSHOT = 4u,
    /**
     * Zero-shutter-lag mode. Application typically request preview and
     * full-resolution data for each frame, and reprocess it to JPEG when a
     * still image is requested by user. Settings must provide highest-quality
     * full-resolution images without compromising preview frame rate. 3A on
     * auto.
     */
    ZERO_SHUTTER_LAG = 5u,
    /**
     * A basic template for direct application control of capture
     * parameters. All automatic control is disabled (auto-exposure, auto-white
     * balance, auto-focus), and post-processing parameters are set to preview
     * quality. The manual capture parameters (exposure, sensitivity, etc.)
     * are set to reasonable defaults, but may be overridden by the
     * application depending on the intended use case.
     */
    MANUAL = 6u,
    /**
     * First value for vendor-defined request templates
     */
    VENDOR_TEMPLATE_START = 1073741824u,
};

/**
 * CaptureRequest:
 * 
 * A single request for image capture/buffer reprocessing, sent to the Camera
 * HAL device by the framework in processCaptureRequest().
 * 
 * The request contains the settings to be used for this capture, and the set of
 * output buffers to write the resulting image data in. It may optionally
 * contain an input buffer, in which case the request is for reprocessing that
 * input buffer instead of capturing a new image with the camera sensor. The
 * capture is identified by the frameNumber.
 * 
 * In response, the camera HAL device must send a CaptureResult
 * structure asynchronously to the framework, using the processCaptureResult()
 * callback.
 */
struct CaptureRequest final {
    uint32_t frameNumber __attribute__ ((aligned(4)));
    uint64_t fmqSettingsSize __attribute__ ((aligned(8)));
    ::android::hardware::hidl_vec<uint8_t> settings __attribute__ ((aligned(8)));
    ::android::hardware::camera::device::V3_2::StreamBuffer inputBuffer __attribute__ ((aligned(8)));
    ::android::hardware::hidl_vec<::android::hardware::camera::device::V3_2::StreamBuffer> outputBuffers __attribute__ ((aligned(8)));
};

static_assert(offsetof(::android::hardware::camera::device::V3_2::CaptureRequest, frameNumber) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::CaptureRequest, fmqSettingsSize) == 8, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::CaptureRequest, settings) == 16, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::CaptureRequest, inputBuffer) == 32, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::CaptureRequest, outputBuffers) == 104, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V3_2::CaptureRequest) == 120, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V3_2::CaptureRequest) == 8, "wrong alignment");

/**
 * CaptureResult:
 * 
 * The result of a single capture/reprocess by the camera HAL device. This is
 * sent to the framework asynchronously with processCaptureResult(), in
 * response to a single capture request sent to the HAL with
 * processCaptureRequest(). Multiple processCaptureResult() calls may be
 * performed by the HAL for each request.
 * 
 * Each call, all with the same frame
 * number, may contain some subset of the output buffers, and/or the result
 * metadata.
 * 
 * The result structure contains the output metadata from this capture, and the
 * set of output buffers that have been/will be filled for this capture. Each
 * output buffer may come with a release sync fence that the framework must wait
 * on before reading, in case the buffer has not yet been filled by the HAL.
 * 
 * The metadata may be provided multiple times for a single frame number. The
 * framework must accumulate together the final result set by combining each
 * partial result together into the total result set.
 * 
 * If an input buffer is given in a request, the HAL must return it in one of
 * the processCaptureResult calls, and the call may be to just return the
 * input buffer, without metadata and output buffers; the sync fences must be
 * handled the same way they are done for output buffers.
 * 
 * Performance considerations:
 * 
 * Applications receive these partial results immediately, so sending partial
 * results is a highly recommended performance optimization to avoid the total
 * pipeline latency before sending the results for what is known very early on
 * in the pipeline.
 * 
 * A typical use case might be calculating the AF state halfway through the
 * pipeline; by sending the state back to the framework immediately, we get a
 * 50% performance increase and perceived responsiveness of the auto-focus.
 * 
 */
struct CaptureResult final {
    uint32_t frameNumber __attribute__ ((aligned(4)));
    uint64_t fmqResultSize __attribute__ ((aligned(8)));
    ::android::hardware::hidl_vec<uint8_t> result __attribute__ ((aligned(8)));
    ::android::hardware::hidl_vec<::android::hardware::camera::device::V3_2::StreamBuffer> outputBuffers __attribute__ ((aligned(8)));
    ::android::hardware::camera::device::V3_2::StreamBuffer inputBuffer __attribute__ ((aligned(8)));
    uint32_t partialResult __attribute__ ((aligned(4)));
};

static_assert(offsetof(::android::hardware::camera::device::V3_2::CaptureResult, frameNumber) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::CaptureResult, fmqResultSize) == 8, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::CaptureResult, result) == 16, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::CaptureResult, outputBuffers) == 32, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::CaptureResult, inputBuffer) == 48, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::CaptureResult, partialResult) == 120, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V3_2::CaptureResult) == 128, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V3_2::CaptureResult) == 8, "wrong alignment");

/**
 * BufferCache:
 * 
 * A list of cached bufferIds associated with a certain stream.
 * Buffers are passed between camera service and camera HAL via bufferId except
 * the first time a new buffer is being passed to HAL in CaptureRequest. Camera
 * service and camera HAL therefore need to maintain a cached map of bufferId
 * and corresponing native handle.
 * 
 */
struct BufferCache final {
    int32_t streamId __attribute__ ((aligned(4)));
    uint64_t bufferId __attribute__ ((aligned(8)));
};

static_assert(offsetof(::android::hardware::camera::device::V3_2::BufferCache, streamId) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V3_2::BufferCache, bufferId) == 8, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V3_2::BufferCache) == 16, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V3_2::BufferCache) == 8, "wrong alignment");

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::StreamType lhs, const ::android::hardware::camera::device::V3_2::StreamType rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::StreamType rhs) {
    return static_cast<uint32_t>(lhs | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::StreamType lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | rhs);
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::StreamType lhs, const ::android::hardware::camera::device::V3_2::StreamType rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::StreamType rhs) {
    return static_cast<uint32_t>(lhs & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::StreamType lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & rhs);
}

constexpr uint32_t &operator|=(uint32_t& v, const ::android::hardware::camera::device::V3_2::StreamType e) {
    v |= static_cast<uint32_t>(e);
    return v;
}

constexpr uint32_t &operator&=(uint32_t& v, const ::android::hardware::camera::device::V3_2::StreamType e) {
    v &= static_cast<uint32_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint32_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V3_2::StreamType>(uint32_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V3_2::StreamType> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V3_2::StreamType::OUTPUT) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamType::OUTPUT)) {
        os += (first ? "" : " | ");
        os += "OUTPUT";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamType::OUTPUT;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamType::INPUT) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamType::INPUT)) {
        os += (first ? "" : " | ");
        os += "INPUT";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamType::INPUT;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V3_2::StreamType o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V3_2::StreamType::OUTPUT) {
        return "OUTPUT";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamType::INPUT) {
        return "INPUT";
    }
    std::string os;
    os += toHexString(static_cast<uint32_t>(o));
    return os;
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::StreamRotation lhs, const ::android::hardware::camera::device::V3_2::StreamRotation rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::StreamRotation rhs) {
    return static_cast<uint32_t>(lhs | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::StreamRotation lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | rhs);
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::StreamRotation lhs, const ::android::hardware::camera::device::V3_2::StreamRotation rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::StreamRotation rhs) {
    return static_cast<uint32_t>(lhs & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::StreamRotation lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & rhs);
}

constexpr uint32_t &operator|=(uint32_t& v, const ::android::hardware::camera::device::V3_2::StreamRotation e) {
    v |= static_cast<uint32_t>(e);
    return v;
}

constexpr uint32_t &operator&=(uint32_t& v, const ::android::hardware::camera::device::V3_2::StreamRotation e) {
    v &= static_cast<uint32_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint32_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V3_2::StreamRotation>(uint32_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V3_2::StreamRotation> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_0) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_0)) {
        os += (first ? "" : " | ");
        os += "ROTATION_0";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_0;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_90) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_90)) {
        os += (first ? "" : " | ");
        os += "ROTATION_90";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_90;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_180) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_180)) {
        os += (first ? "" : " | ");
        os += "ROTATION_180";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_180;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_270) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_270)) {
        os += (first ? "" : " | ");
        os += "ROTATION_270";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_270;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V3_2::StreamRotation o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_0) {
        return "ROTATION_0";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_90) {
        return "ROTATION_90";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_180) {
        return "ROTATION_180";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_270) {
        return "ROTATION_270";
    }
    std::string os;
    os += toHexString(static_cast<uint32_t>(o));
    return os;
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::StreamConfigurationMode lhs, const ::android::hardware::camera::device::V3_2::StreamConfigurationMode rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::StreamConfigurationMode rhs) {
    return static_cast<uint32_t>(lhs | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::StreamConfigurationMode lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | rhs);
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::StreamConfigurationMode lhs, const ::android::hardware::camera::device::V3_2::StreamConfigurationMode rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::StreamConfigurationMode rhs) {
    return static_cast<uint32_t>(lhs & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::StreamConfigurationMode lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & rhs);
}

constexpr uint32_t &operator|=(uint32_t& v, const ::android::hardware::camera::device::V3_2::StreamConfigurationMode e) {
    v |= static_cast<uint32_t>(e);
    return v;
}

constexpr uint32_t &operator&=(uint32_t& v, const ::android::hardware::camera::device::V3_2::StreamConfigurationMode e) {
    v &= static_cast<uint32_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint32_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V3_2::StreamConfigurationMode>(uint32_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V3_2::StreamConfigurationMode> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V3_2::StreamConfigurationMode::NORMAL_MODE) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamConfigurationMode::NORMAL_MODE)) {
        os += (first ? "" : " | ");
        os += "NORMAL_MODE";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamConfigurationMode::NORMAL_MODE;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamConfigurationMode::CONSTRAINED_HIGH_SPEED_MODE) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamConfigurationMode::CONSTRAINED_HIGH_SPEED_MODE)) {
        os += (first ? "" : " | ");
        os += "CONSTRAINED_HIGH_SPEED_MODE";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamConfigurationMode::CONSTRAINED_HIGH_SPEED_MODE;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_0) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_0)) {
        os += (first ? "" : " | ");
        os += "VENDOR_MODE_0";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_0;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_1) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_1)) {
        os += (first ? "" : " | ");
        os += "VENDOR_MODE_1";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_1;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_2) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_2)) {
        os += (first ? "" : " | ");
        os += "VENDOR_MODE_2";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_2;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_3) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_3)) {
        os += (first ? "" : " | ");
        os += "VENDOR_MODE_3";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_3;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_4) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_4)) {
        os += (first ? "" : " | ");
        os += "VENDOR_MODE_4";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_4;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_5) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_5)) {
        os += (first ? "" : " | ");
        os += "VENDOR_MODE_5";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_5;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_6) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_6)) {
        os += (first ? "" : " | ");
        os += "VENDOR_MODE_6";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_6;
    }
    if ((o & ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_7) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_7)) {
        os += (first ? "" : " | ");
        os += "VENDOR_MODE_7";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_7;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V3_2::StreamConfigurationMode o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V3_2::StreamConfigurationMode::NORMAL_MODE) {
        return "NORMAL_MODE";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamConfigurationMode::CONSTRAINED_HIGH_SPEED_MODE) {
        return "CONSTRAINED_HIGH_SPEED_MODE";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_0) {
        return "VENDOR_MODE_0";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_1) {
        return "VENDOR_MODE_1";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_2) {
        return "VENDOR_MODE_2";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_3) {
        return "VENDOR_MODE_3";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_4) {
        return "VENDOR_MODE_4";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_5) {
        return "VENDOR_MODE_5";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_6) {
        return "VENDOR_MODE_6";
    }
    if (o == ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_7) {
        return "VENDOR_MODE_7";
    }
    std::string os;
    os += toHexString(static_cast<uint32_t>(o));
    return os;
}

static inline std::string toString(const ::android::hardware::camera::device::V3_2::Stream& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".id = ";
    os += ::android::hardware::toString(o.id);
    os += ", .streamType = ";
    os += ::android::hardware::camera::device::V3_2::toString(o.streamType);
    os += ", .width = ";
    os += ::android::hardware::toString(o.width);
    os += ", .height = ";
    os += ::android::hardware::toString(o.height);
    os += ", .format = ";
    os += ::android::hardware::graphics::common::V1_0::toString(o.format);
    os += ", .usage = ";
    os += ::android::hardware::graphics::common::V1_0::toString<::android::hardware::graphics::common::V1_0::BufferUsage>(o.usage);
    os += ", .dataSpace = ";
    os += ::android::hardware::graphics::common::V1_0::toString<::android::hardware::graphics::common::V1_0::Dataspace>(o.dataSpace);
    os += ", .rotation = ";
    os += ::android::hardware::camera::device::V3_2::toString(o.rotation);
    os += "}"; return os;
}

static inline bool operator==(const ::android::hardware::camera::device::V3_2::Stream& lhs, const ::android::hardware::camera::device::V3_2::Stream& rhs) {
    if (lhs.id != rhs.id) {
        return false;
    }
    if (lhs.streamType != rhs.streamType) {
        return false;
    }
    if (lhs.width != rhs.width) {
        return false;
    }
    if (lhs.height != rhs.height) {
        return false;
    }
    if (lhs.format != rhs.format) {
        return false;
    }
    if (lhs.usage != rhs.usage) {
        return false;
    }
    if (lhs.dataSpace != rhs.dataSpace) {
        return false;
    }
    if (lhs.rotation != rhs.rotation) {
        return false;
    }
    return true;
}

static inline bool operator!=(const ::android::hardware::camera::device::V3_2::Stream& lhs,const ::android::hardware::camera::device::V3_2::Stream& rhs){
    return !(lhs == rhs);
}

static inline std::string toString(const ::android::hardware::camera::device::V3_2::StreamConfiguration& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".streams = ";
    os += ::android::hardware::toString(o.streams);
    os += ", .operationMode = ";
    os += ::android::hardware::camera::device::V3_2::toString(o.operationMode);
    os += "}"; return os;
}

static inline bool operator==(const ::android::hardware::camera::device::V3_2::StreamConfiguration& lhs, const ::android::hardware::camera::device::V3_2::StreamConfiguration& rhs) {
    if (lhs.streams != rhs.streams) {
        return false;
    }
    if (lhs.operationMode != rhs.operationMode) {
        return false;
    }
    return true;
}

static inline bool operator!=(const ::android::hardware::camera::device::V3_2::StreamConfiguration& lhs,const ::android::hardware::camera::device::V3_2::StreamConfiguration& rhs){
    return !(lhs == rhs);
}

static inline std::string toString(const ::android::hardware::camera::device::V3_2::HalStream& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".id = ";
    os += ::android::hardware::toString(o.id);
    os += ", .overrideFormat = ";
    os += ::android::hardware::graphics::common::V1_0::toString(o.overrideFormat);
    os += ", .producerUsage = ";
    os += ::android::hardware::graphics::common::V1_0::toString<::android::hardware::graphics::common::V1_0::BufferUsage>(o.producerUsage);
    os += ", .consumerUsage = ";
    os += ::android::hardware::graphics::common::V1_0::toString<::android::hardware::graphics::common::V1_0::BufferUsage>(o.consumerUsage);
    os += ", .maxBuffers = ";
    os += ::android::hardware::toString(o.maxBuffers);
    os += "}"; return os;
}

static inline bool operator==(const ::android::hardware::camera::device::V3_2::HalStream& lhs, const ::android::hardware::camera::device::V3_2::HalStream& rhs) {
    if (lhs.id != rhs.id) {
        return false;
    }
    if (lhs.overrideFormat != rhs.overrideFormat) {
        return false;
    }
    if (lhs.producerUsage != rhs.producerUsage) {
        return false;
    }
    if (lhs.consumerUsage != rhs.consumerUsage) {
        return false;
    }
    if (lhs.maxBuffers != rhs.maxBuffers) {
        return false;
    }
    return true;
}

static inline bool operator!=(const ::android::hardware::camera::device::V3_2::HalStream& lhs,const ::android::hardware::camera::device::V3_2::HalStream& rhs){
    return !(lhs == rhs);
}

static inline std::string toString(const ::android::hardware::camera::device::V3_2::HalStreamConfiguration& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".streams = ";
    os += ::android::hardware::toString(o.streams);
    os += "}"; return os;
}

static inline bool operator==(const ::android::hardware::camera::device::V3_2::HalStreamConfiguration& lhs, const ::android::hardware::camera::device::V3_2::HalStreamConfiguration& rhs) {
    if (lhs.streams != rhs.streams) {
        return false;
    }
    return true;
}

static inline bool operator!=(const ::android::hardware::camera::device::V3_2::HalStreamConfiguration& lhs,const ::android::hardware::camera::device::V3_2::HalStreamConfiguration& rhs){
    return !(lhs == rhs);
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::BufferStatus lhs, const ::android::hardware::camera::device::V3_2::BufferStatus rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::BufferStatus rhs) {
    return static_cast<uint32_t>(lhs | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::BufferStatus lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | rhs);
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::BufferStatus lhs, const ::android::hardware::camera::device::V3_2::BufferStatus rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::BufferStatus rhs) {
    return static_cast<uint32_t>(lhs & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::BufferStatus lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & rhs);
}

constexpr uint32_t &operator|=(uint32_t& v, const ::android::hardware::camera::device::V3_2::BufferStatus e) {
    v |= static_cast<uint32_t>(e);
    return v;
}

constexpr uint32_t &operator&=(uint32_t& v, const ::android::hardware::camera::device::V3_2::BufferStatus e) {
    v &= static_cast<uint32_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint32_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V3_2::BufferStatus>(uint32_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V3_2::BufferStatus> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V3_2::BufferStatus::OK) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::BufferStatus::OK)) {
        os += (first ? "" : " | ");
        os += "OK";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::BufferStatus::OK;
    }
    if ((o & ::android::hardware::camera::device::V3_2::BufferStatus::ERROR) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::BufferStatus::ERROR)) {
        os += (first ? "" : " | ");
        os += "ERROR";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::BufferStatus::ERROR;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V3_2::BufferStatus o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V3_2::BufferStatus::OK) {
        return "OK";
    }
    if (o == ::android::hardware::camera::device::V3_2::BufferStatus::ERROR) {
        return "ERROR";
    }
    std::string os;
    os += toHexString(static_cast<uint32_t>(o));
    return os;
}

static inline std::string toString(const ::android::hardware::camera::device::V3_2::StreamBuffer& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".streamId = ";
    os += ::android::hardware::toString(o.streamId);
    os += ", .bufferId = ";
    os += ::android::hardware::toString(o.bufferId);
    os += ", .buffer = ";
    os += ::android::hardware::toString(o.buffer);
    os += ", .status = ";
    os += ::android::hardware::camera::device::V3_2::toString(o.status);
    os += ", .acquireFence = ";
    os += ::android::hardware::toString(o.acquireFence);
    os += ", .releaseFence = ";
    os += ::android::hardware::toString(o.releaseFence);
    os += "}"; return os;
}

// operator== and operator!= are not generated for StreamBuffer

constexpr uint16_t operator|(const ::android::hardware::camera::device::V3_2::CameraBlobId lhs, const ::android::hardware::camera::device::V3_2::CameraBlobId rhs) {
    return static_cast<uint16_t>(static_cast<uint16_t>(lhs) | static_cast<uint16_t>(rhs));
}

constexpr uint16_t operator|(const uint16_t lhs, const ::android::hardware::camera::device::V3_2::CameraBlobId rhs) {
    return static_cast<uint16_t>(lhs | static_cast<uint16_t>(rhs));
}

constexpr uint16_t operator|(const ::android::hardware::camera::device::V3_2::CameraBlobId lhs, const uint16_t rhs) {
    return static_cast<uint16_t>(static_cast<uint16_t>(lhs) | rhs);
}

constexpr uint16_t operator&(const ::android::hardware::camera::device::V3_2::CameraBlobId lhs, const ::android::hardware::camera::device::V3_2::CameraBlobId rhs) {
    return static_cast<uint16_t>(static_cast<uint16_t>(lhs) & static_cast<uint16_t>(rhs));
}

constexpr uint16_t operator&(const uint16_t lhs, const ::android::hardware::camera::device::V3_2::CameraBlobId rhs) {
    return static_cast<uint16_t>(lhs & static_cast<uint16_t>(rhs));
}

constexpr uint16_t operator&(const ::android::hardware::camera::device::V3_2::CameraBlobId lhs, const uint16_t rhs) {
    return static_cast<uint16_t>(static_cast<uint16_t>(lhs) & rhs);
}

constexpr uint16_t &operator|=(uint16_t& v, const ::android::hardware::camera::device::V3_2::CameraBlobId e) {
    v |= static_cast<uint16_t>(e);
    return v;
}

constexpr uint16_t &operator&=(uint16_t& v, const ::android::hardware::camera::device::V3_2::CameraBlobId e) {
    v &= static_cast<uint16_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint16_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V3_2::CameraBlobId>(uint16_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V3_2::CameraBlobId> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V3_2::CameraBlobId::JPEG) == static_cast<uint16_t>(::android::hardware::camera::device::V3_2::CameraBlobId::JPEG)) {
        os += (first ? "" : " | ");
        os += "JPEG";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::CameraBlobId::JPEG;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V3_2::CameraBlobId o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V3_2::CameraBlobId::JPEG) {
        return "JPEG";
    }
    std::string os;
    os += toHexString(static_cast<uint16_t>(o));
    return os;
}

static inline std::string toString(const ::android::hardware::camera::device::V3_2::CameraBlob& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".blobId = ";
    os += ::android::hardware::camera::device::V3_2::toString(o.blobId);
    os += ", .blobSize = ";
    os += ::android::hardware::toString(o.blobSize);
    os += "}"; return os;
}

static inline bool operator==(const ::android::hardware::camera::device::V3_2::CameraBlob& lhs, const ::android::hardware::camera::device::V3_2::CameraBlob& rhs) {
    if (lhs.blobId != rhs.blobId) {
        return false;
    }
    if (lhs.blobSize != rhs.blobSize) {
        return false;
    }
    return true;
}

static inline bool operator!=(const ::android::hardware::camera::device::V3_2::CameraBlob& lhs,const ::android::hardware::camera::device::V3_2::CameraBlob& rhs){
    return !(lhs == rhs);
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::MsgType lhs, const ::android::hardware::camera::device::V3_2::MsgType rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::MsgType rhs) {
    return static_cast<uint32_t>(lhs | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::MsgType lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | rhs);
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::MsgType lhs, const ::android::hardware::camera::device::V3_2::MsgType rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::MsgType rhs) {
    return static_cast<uint32_t>(lhs & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::MsgType lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & rhs);
}

constexpr uint32_t &operator|=(uint32_t& v, const ::android::hardware::camera::device::V3_2::MsgType e) {
    v |= static_cast<uint32_t>(e);
    return v;
}

constexpr uint32_t &operator&=(uint32_t& v, const ::android::hardware::camera::device::V3_2::MsgType e) {
    v &= static_cast<uint32_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint32_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V3_2::MsgType>(uint32_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V3_2::MsgType> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V3_2::MsgType::ERROR) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::MsgType::ERROR)) {
        os += (first ? "" : " | ");
        os += "ERROR";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::MsgType::ERROR;
    }
    if ((o & ::android::hardware::camera::device::V3_2::MsgType::SHUTTER) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::MsgType::SHUTTER)) {
        os += (first ? "" : " | ");
        os += "SHUTTER";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::MsgType::SHUTTER;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V3_2::MsgType o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V3_2::MsgType::ERROR) {
        return "ERROR";
    }
    if (o == ::android::hardware::camera::device::V3_2::MsgType::SHUTTER) {
        return "SHUTTER";
    }
    std::string os;
    os += toHexString(static_cast<uint32_t>(o));
    return os;
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::ErrorCode lhs, const ::android::hardware::camera::device::V3_2::ErrorCode rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::ErrorCode rhs) {
    return static_cast<uint32_t>(lhs | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::ErrorCode lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | rhs);
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::ErrorCode lhs, const ::android::hardware::camera::device::V3_2::ErrorCode rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::ErrorCode rhs) {
    return static_cast<uint32_t>(lhs & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::ErrorCode lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & rhs);
}

constexpr uint32_t &operator|=(uint32_t& v, const ::android::hardware::camera::device::V3_2::ErrorCode e) {
    v |= static_cast<uint32_t>(e);
    return v;
}

constexpr uint32_t &operator&=(uint32_t& v, const ::android::hardware::camera::device::V3_2::ErrorCode e) {
    v &= static_cast<uint32_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint32_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V3_2::ErrorCode>(uint32_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V3_2::ErrorCode> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_DEVICE) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::ErrorCode::ERROR_DEVICE)) {
        os += (first ? "" : " | ");
        os += "ERROR_DEVICE";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_DEVICE;
    }
    if ((o & ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_REQUEST) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::ErrorCode::ERROR_REQUEST)) {
        os += (first ? "" : " | ");
        os += "ERROR_REQUEST";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_REQUEST;
    }
    if ((o & ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_RESULT) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::ErrorCode::ERROR_RESULT)) {
        os += (first ? "" : " | ");
        os += "ERROR_RESULT";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_RESULT;
    }
    if ((o & ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_BUFFER) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::ErrorCode::ERROR_BUFFER)) {
        os += (first ? "" : " | ");
        os += "ERROR_BUFFER";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_BUFFER;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V3_2::ErrorCode o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_DEVICE) {
        return "ERROR_DEVICE";
    }
    if (o == ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_REQUEST) {
        return "ERROR_REQUEST";
    }
    if (o == ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_RESULT) {
        return "ERROR_RESULT";
    }
    if (o == ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_BUFFER) {
        return "ERROR_BUFFER";
    }
    std::string os;
    os += toHexString(static_cast<uint32_t>(o));
    return os;
}

static inline std::string toString(const ::android::hardware::camera::device::V3_2::ErrorMsg& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".frameNumber = ";
    os += ::android::hardware::toString(o.frameNumber);
    os += ", .errorStreamId = ";
    os += ::android::hardware::toString(o.errorStreamId);
    os += ", .errorCode = ";
    os += ::android::hardware::camera::device::V3_2::toString(o.errorCode);
    os += "}"; return os;
}

static inline bool operator==(const ::android::hardware::camera::device::V3_2::ErrorMsg& lhs, const ::android::hardware::camera::device::V3_2::ErrorMsg& rhs) {
    if (lhs.frameNumber != rhs.frameNumber) {
        return false;
    }
    if (lhs.errorStreamId != rhs.errorStreamId) {
        return false;
    }
    if (lhs.errorCode != rhs.errorCode) {
        return false;
    }
    return true;
}

static inline bool operator!=(const ::android::hardware::camera::device::V3_2::ErrorMsg& lhs,const ::android::hardware::camera::device::V3_2::ErrorMsg& rhs){
    return !(lhs == rhs);
}

static inline std::string toString(const ::android::hardware::camera::device::V3_2::ShutterMsg& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".frameNumber = ";
    os += ::android::hardware::toString(o.frameNumber);
    os += ", .timestamp = ";
    os += ::android::hardware::toString(o.timestamp);
    os += "}"; return os;
}

static inline bool operator==(const ::android::hardware::camera::device::V3_2::ShutterMsg& lhs, const ::android::hardware::camera::device::V3_2::ShutterMsg& rhs) {
    if (lhs.frameNumber != rhs.frameNumber) {
        return false;
    }
    if (lhs.timestamp != rhs.timestamp) {
        return false;
    }
    return true;
}

static inline bool operator!=(const ::android::hardware::camera::device::V3_2::ShutterMsg& lhs,const ::android::hardware::camera::device::V3_2::ShutterMsg& rhs){
    return !(lhs == rhs);
}

static inline std::string toString(const ::android::hardware::camera::device::V3_2::NotifyMsg::Message& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".error = ";
    os += ::android::hardware::camera::device::V3_2::toString(o.error);
    os += ", .shutter = ";
    os += ::android::hardware::camera::device::V3_2::toString(o.shutter);
    os += "}"; return os;
}

// operator== and operator!= are not generated for Message

static inline std::string toString(const ::android::hardware::camera::device::V3_2::NotifyMsg& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".type = ";
    os += ::android::hardware::camera::device::V3_2::toString(o.type);
    os += ", .msg = ";
    os += ::android::hardware::camera::device::V3_2::toString(o.msg);
    os += "}"; return os;
}

// operator== and operator!= are not generated for NotifyMsg

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::RequestTemplate lhs, const ::android::hardware::camera::device::V3_2::RequestTemplate rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::RequestTemplate rhs) {
    return static_cast<uint32_t>(lhs | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V3_2::RequestTemplate lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | rhs);
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::RequestTemplate lhs, const ::android::hardware::camera::device::V3_2::RequestTemplate rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const uint32_t lhs, const ::android::hardware::camera::device::V3_2::RequestTemplate rhs) {
    return static_cast<uint32_t>(lhs & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V3_2::RequestTemplate lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & rhs);
}

constexpr uint32_t &operator|=(uint32_t& v, const ::android::hardware::camera::device::V3_2::RequestTemplate e) {
    v |= static_cast<uint32_t>(e);
    return v;
}

constexpr uint32_t &operator&=(uint32_t& v, const ::android::hardware::camera::device::V3_2::RequestTemplate e) {
    v &= static_cast<uint32_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint32_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V3_2::RequestTemplate>(uint32_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V3_2::RequestTemplate> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V3_2::RequestTemplate::PREVIEW) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::RequestTemplate::PREVIEW)) {
        os += (first ? "" : " | ");
        os += "PREVIEW";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::RequestTemplate::PREVIEW;
    }
    if ((o & ::android::hardware::camera::device::V3_2::RequestTemplate::STILL_CAPTURE) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::RequestTemplate::STILL_CAPTURE)) {
        os += (first ? "" : " | ");
        os += "STILL_CAPTURE";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::RequestTemplate::STILL_CAPTURE;
    }
    if ((o & ::android::hardware::camera::device::V3_2::RequestTemplate::VIDEO_RECORD) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::RequestTemplate::VIDEO_RECORD)) {
        os += (first ? "" : " | ");
        os += "VIDEO_RECORD";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::RequestTemplate::VIDEO_RECORD;
    }
    if ((o & ::android::hardware::camera::device::V3_2::RequestTemplate::VIDEO_SNAPSHOT) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::RequestTemplate::VIDEO_SNAPSHOT)) {
        os += (first ? "" : " | ");
        os += "VIDEO_SNAPSHOT";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::RequestTemplate::VIDEO_SNAPSHOT;
    }
    if ((o & ::android::hardware::camera::device::V3_2::RequestTemplate::ZERO_SHUTTER_LAG) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::RequestTemplate::ZERO_SHUTTER_LAG)) {
        os += (first ? "" : " | ");
        os += "ZERO_SHUTTER_LAG";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::RequestTemplate::ZERO_SHUTTER_LAG;
    }
    if ((o & ::android::hardware::camera::device::V3_2::RequestTemplate::MANUAL) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::RequestTemplate::MANUAL)) {
        os += (first ? "" : " | ");
        os += "MANUAL";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::RequestTemplate::MANUAL;
    }
    if ((o & ::android::hardware::camera::device::V3_2::RequestTemplate::VENDOR_TEMPLATE_START) == static_cast<uint32_t>(::android::hardware::camera::device::V3_2::RequestTemplate::VENDOR_TEMPLATE_START)) {
        os += (first ? "" : " | ");
        os += "VENDOR_TEMPLATE_START";
        first = false;
        flipped |= ::android::hardware::camera::device::V3_2::RequestTemplate::VENDOR_TEMPLATE_START;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V3_2::RequestTemplate o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V3_2::RequestTemplate::PREVIEW) {
        return "PREVIEW";
    }
    if (o == ::android::hardware::camera::device::V3_2::RequestTemplate::STILL_CAPTURE) {
        return "STILL_CAPTURE";
    }
    if (o == ::android::hardware::camera::device::V3_2::RequestTemplate::VIDEO_RECORD) {
        return "VIDEO_RECORD";
    }
    if (o == ::android::hardware::camera::device::V3_2::RequestTemplate::VIDEO_SNAPSHOT) {
        return "VIDEO_SNAPSHOT";
    }
    if (o == ::android::hardware::camera::device::V3_2::RequestTemplate::ZERO_SHUTTER_LAG) {
        return "ZERO_SHUTTER_LAG";
    }
    if (o == ::android::hardware::camera::device::V3_2::RequestTemplate::MANUAL) {
        return "MANUAL";
    }
    if (o == ::android::hardware::camera::device::V3_2::RequestTemplate::VENDOR_TEMPLATE_START) {
        return "VENDOR_TEMPLATE_START";
    }
    std::string os;
    os += toHexString(static_cast<uint32_t>(o));
    return os;
}

static inline std::string toString(const ::android::hardware::camera::device::V3_2::CaptureRequest& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".frameNumber = ";
    os += ::android::hardware::toString(o.frameNumber);
    os += ", .fmqSettingsSize = ";
    os += ::android::hardware::toString(o.fmqSettingsSize);
    os += ", .settings = ";
    os += ::android::hardware::toString(o.settings);
    os += ", .inputBuffer = ";
    os += ::android::hardware::camera::device::V3_2::toString(o.inputBuffer);
    os += ", .outputBuffers = ";
    os += ::android::hardware::toString(o.outputBuffers);
    os += "}"; return os;
}

// operator== and operator!= are not generated for CaptureRequest

static inline std::string toString(const ::android::hardware::camera::device::V3_2::CaptureResult& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".frameNumber = ";
    os += ::android::hardware::toString(o.frameNumber);
    os += ", .fmqResultSize = ";
    os += ::android::hardware::toString(o.fmqResultSize);
    os += ", .result = ";
    os += ::android::hardware::toString(o.result);
    os += ", .outputBuffers = ";
    os += ::android::hardware::toString(o.outputBuffers);
    os += ", .inputBuffer = ";
    os += ::android::hardware::camera::device::V3_2::toString(o.inputBuffer);
    os += ", .partialResult = ";
    os += ::android::hardware::toString(o.partialResult);
    os += "}"; return os;
}

// operator== and operator!= are not generated for CaptureResult

static inline std::string toString(const ::android::hardware::camera::device::V3_2::BufferCache& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".streamId = ";
    os += ::android::hardware::toString(o.streamId);
    os += ", .bufferId = ";
    os += ::android::hardware::toString(o.bufferId);
    os += "}"; return os;
}

static inline bool operator==(const ::android::hardware::camera::device::V3_2::BufferCache& lhs, const ::android::hardware::camera::device::V3_2::BufferCache& rhs) {
    if (lhs.streamId != rhs.streamId) {
        return false;
    }
    if (lhs.bufferId != rhs.bufferId) {
        return false;
    }
    return true;
}

static inline bool operator!=(const ::android::hardware::camera::device::V3_2::BufferCache& lhs,const ::android::hardware::camera::device::V3_2::BufferCache& rhs){
    return !(lhs == rhs);
}


}  // namespace V3_2
}  // namespace device
}  // namespace camera
}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V3_2::StreamType>
{
    const ::android::hardware::camera::device::V3_2::StreamType* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V3_2::StreamType* end() { return begin() + 2; }
    private:
    static const ::android::hardware::camera::device::V3_2::StreamType* static_begin() {
        static const ::android::hardware::camera::device::V3_2::StreamType kVals[2] {
            ::android::hardware::camera::device::V3_2::StreamType::OUTPUT,
            ::android::hardware::camera::device::V3_2::StreamType::INPUT,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V3_2::StreamRotation>
{
    const ::android::hardware::camera::device::V3_2::StreamRotation* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V3_2::StreamRotation* end() { return begin() + 4; }
    private:
    static const ::android::hardware::camera::device::V3_2::StreamRotation* static_begin() {
        static const ::android::hardware::camera::device::V3_2::StreamRotation kVals[4] {
            ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_0,
            ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_90,
            ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_180,
            ::android::hardware::camera::device::V3_2::StreamRotation::ROTATION_270,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V3_2::StreamConfigurationMode>
{
    const ::android::hardware::camera::device::V3_2::StreamConfigurationMode* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V3_2::StreamConfigurationMode* end() { return begin() + 10; }
    private:
    static const ::android::hardware::camera::device::V3_2::StreamConfigurationMode* static_begin() {
        static const ::android::hardware::camera::device::V3_2::StreamConfigurationMode kVals[10] {
            ::android::hardware::camera::device::V3_2::StreamConfigurationMode::NORMAL_MODE,
            ::android::hardware::camera::device::V3_2::StreamConfigurationMode::CONSTRAINED_HIGH_SPEED_MODE,
            ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_0,
            ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_1,
            ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_2,
            ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_3,
            ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_4,
            ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_5,
            ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_6,
            ::android::hardware::camera::device::V3_2::StreamConfigurationMode::VENDOR_MODE_7,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V3_2::BufferStatus>
{
    const ::android::hardware::camera::device::V3_2::BufferStatus* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V3_2::BufferStatus* end() { return begin() + 2; }
    private:
    static const ::android::hardware::camera::device::V3_2::BufferStatus* static_begin() {
        static const ::android::hardware::camera::device::V3_2::BufferStatus kVals[2] {
            ::android::hardware::camera::device::V3_2::BufferStatus::OK,
            ::android::hardware::camera::device::V3_2::BufferStatus::ERROR,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V3_2::CameraBlobId>
{
    const ::android::hardware::camera::device::V3_2::CameraBlobId* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V3_2::CameraBlobId* end() { return begin() + 1; }
    private:
    static const ::android::hardware::camera::device::V3_2::CameraBlobId* static_begin() {
        static const ::android::hardware::camera::device::V3_2::CameraBlobId kVals[1] {
            ::android::hardware::camera::device::V3_2::CameraBlobId::JPEG,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V3_2::MsgType>
{
    const ::android::hardware::camera::device::V3_2::MsgType* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V3_2::MsgType* end() { return begin() + 2; }
    private:
    static const ::android::hardware::camera::device::V3_2::MsgType* static_begin() {
        static const ::android::hardware::camera::device::V3_2::MsgType kVals[2] {
            ::android::hardware::camera::device::V3_2::MsgType::ERROR,
            ::android::hardware::camera::device::V3_2::MsgType::SHUTTER,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V3_2::ErrorCode>
{
    const ::android::hardware::camera::device::V3_2::ErrorCode* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V3_2::ErrorCode* end() { return begin() + 4; }
    private:
    static const ::android::hardware::camera::device::V3_2::ErrorCode* static_begin() {
        static const ::android::hardware::camera::device::V3_2::ErrorCode kVals[4] {
            ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_DEVICE,
            ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_REQUEST,
            ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_RESULT,
            ::android::hardware::camera::device::V3_2::ErrorCode::ERROR_BUFFER,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V3_2::RequestTemplate>
{
    const ::android::hardware::camera::device::V3_2::RequestTemplate* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V3_2::RequestTemplate* end() { return begin() + 7; }
    private:
    static const ::android::hardware::camera::device::V3_2::RequestTemplate* static_begin() {
        static const ::android::hardware::camera::device::V3_2::RequestTemplate kVals[7] {
            ::android::hardware::camera::device::V3_2::RequestTemplate::PREVIEW,
            ::android::hardware::camera::device::V3_2::RequestTemplate::STILL_CAPTURE,
            ::android::hardware::camera::device::V3_2::RequestTemplate::VIDEO_RECORD,
            ::android::hardware::camera::device::V3_2::RequestTemplate::VIDEO_SNAPSHOT,
            ::android::hardware::camera::device::V3_2::RequestTemplate::ZERO_SHUTTER_LAG,
            ::android::hardware::camera::device::V3_2::RequestTemplate::MANUAL,
            ::android::hardware::camera::device::V3_2::RequestTemplate::VENDOR_TEMPLATE_START,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android

#endif  // HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V3_2_TYPES_H
