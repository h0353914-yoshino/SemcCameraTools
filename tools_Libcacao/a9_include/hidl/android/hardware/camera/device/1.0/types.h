#ifndef HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V1_0_TYPES_H
#define HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V1_0_TYPES_H

#include <hidl/HidlSupport.h>
#include <hidl/MQDescriptor.h>
#include <utils/NativeHandle.h>
#include <utils/misc.h>

namespace android {
namespace hardware {
namespace camera {
namespace device {
namespace V1_0 {

// Forward declaration for forward reference support:
enum class CameraFacing : uint32_t;
struct CameraInfo;
enum class FrameCallbackFlag : uint32_t;
enum class CommandType : uint32_t;
enum class NotifyCallbackMsg : uint32_t;
enum class DataCallbackMsg : uint32_t;
struct CameraFace;
struct CameraFrameMetadata;
struct HandleTimestampMessage;
struct VideoFrameMessage;

enum class CameraFacing : uint32_t {
    /**
     * The facing of the camera is opposite to that of the screen.  */
    BACK = 0u,
    /**
     * The facing of the camera is the same as that of the screen.  */
    FRONT = 1u,
    /**
     * The facing of the camera is not fixed relative to the screen.
     * The cameras with this facing are external cameras, e.g. USB cameras.
     */
    EXTERNAL = 2u,
};

/**
 * Basic information about a camera device, always accessible via
 * ICameraDevice::getCameraInfo().
 */
struct CameraInfo final {
    ::android::hardware::camera::device::V1_0::CameraFacing facing __attribute__ ((aligned(4)));
    uint32_t orientation __attribute__ ((aligned(4)));
};

static_assert(offsetof(::android::hardware::camera::device::V1_0::CameraInfo, facing) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V1_0::CameraInfo, orientation) == 4, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V1_0::CameraInfo) == 8, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V1_0::CameraInfo) == 4, "wrong alignment");

/**
 * Message types for ICameraDevice@1.0::enableMsgType()/disableMsgType()
 * 
 * A set of bit masks for specifying how the received preview frames are
 * handled before the previewCallback() call.
 * 
 * The least significant 3 bits of an "int" value are used for this purpose:
 * 
 * ..... 0 0 0
 *       ^ ^ ^
 *       | | |---------> determine whether the callback is enabled or not
 *       | |-----------> determine whether the callback is one-shot or not
 *       |-------------> determine whether the frame is copied out or not
 * 
 * WARNING: When a frame is sent directly without copying, it is the frame
 * receiver's responsiblity to make sure that the frame data won't get
 * corrupted by subsequent preview frames filled by the camera. This flag is
 * recommended only when copying out data brings significant performance price
 * and the handling/processing of the received frame data is always faster than
 * the preview frame rate so that data corruption won't occur.
 * 
 * For instance,
 * 1. 0x00 disables the callback. In this case, copy out and one shot bits
 *    are ignored.
 * 2. 0x01 enables a callback without copying out the received frames. A
 *    typical use case is the Camcorder application to avoid making costly
 *    frame copies.
 * 3. 0x05 is enabling a callback with frame copied out repeatedly. A typical
 *    use case is the Camera application.
 * 4. 0x07 is enabling a callback with frame copied out only once. A typical
 *    use case is the Barcode scanner application.
 */
enum class FrameCallbackFlag : uint32_t {
    ENABLE_MASK = 1u,
    ONE_SHOT_MASK = 2u,
    COPY_OUT_MASK = 4u,
    /**
     * Typical use cases  */
    NOOP = 0u,
    CAMCORDER = 1u,
    CAMERA = 5u,
    BARCODE_SCANNER = 7u,
};

typedef ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V1_0::FrameCallbackFlag> FrameCallbackFlags;

/**
 * Subset of commands in /system/core/include/system/camera.h relevant for
 * ICameraDevice@1.0::sendCommand()
 */
enum class CommandType : uint32_t {
    START_SMOOTH_ZOOM = 1u,
    STOP_SMOOTH_ZOOM = 2u,
    /**
     * Start the face detection. This must be called only after preview is
     * started.  The camera must notify the listener of CAMERA_MSG_FACE and the
     * detected faces in the preview frame. The detected faces may be the same
     * as the previous ones. Apps must call CAMERA_CMD_STOP_FACE_DETECTION to
     * stop the face detection. This method is supported if CameraParameters
     * KEY_MAX_NUM_HW_DETECTED_FACES or KEY_MAX_NUM_SW_DETECTED_FACES is bigger
     * than 0. Hardware and software face detection must not be running at the
     * same time. If the face detection has started, apps must not send this
     * again.
     * 
     * In hardware face detection mode, CameraParameters KEY_WHITE_BALANCE,
     * KEY_FOCUS_AREAS and KEY_METERING_AREAS have no effect.
     * 
     * arg1 is the face detection type. It can be CAMERA_FACE_DETECTION_HW or
     * CAMERA_FACE_DETECTION_SW. If the type of face detection requested is not
     * supported, the HAL must return BAD_VALUE.
     */
    START_FACE_DETECTION = 6u,
    /**
     * Stop the face detection.
     */
    STOP_FACE_DETECTION = 7u,
    /**
     * Enable/disable focus move callback (CAMERA_MSG_FOCUS_MOVE). Passing
     * arg1 = 0 must disable, while passing arg1 = 1 must enable the callback.
     */
    ENABLE_FOCUS_MOVE_MSG = 8u,
    /**
     * Configure an explicit format to use for video recording metadata mode.
     * This can be used to switch the format from the
     * default IMPLEMENTATION_DEFINED gralloc format to some other
     * device-supported format, and the default dataspace from the BT_709 color
     * space to some other device-supported dataspace. arg1 is the HAL pixel
     * format, and arg2 is the HAL dataSpace. This command returns
     * INVALID_OPERATION error if it is sent after video recording is started,
     * or the command is not supported at all.
     * 
     * If the gralloc format is set to a format other than
     * IMPLEMENTATION_DEFINED, then HALv3 devices must use gralloc usage flags
     * of SW_READ_OFTEN.
     */
    SET_VIDEO_FORMAT = 11u,
};

/**
 * Message types for ICameraDevice1Callback::notifyCallback()
 */
enum class NotifyCallbackMsg : uint32_t {
    ERROR = 1u,
    SHUTTER = 2u,
    FOCUS = 4u,
    ZOOM = 8u,
    FOCUS_MOVE = 2048u,
};

/**
 * Message types for ICameraDevice1Callback::dataCallback() and
 * ICameraDevice1Callback::dataCallbackTimestamp()
 */
enum class DataCallbackMsg : uint32_t {
    PREVIEW_FRAME = 16u,
    VIDEO_FRAME = 32u,
    POSTVIEW_FRAME = 64u,
    RAW_IMAGE = 128u,
    COMPRESSED_IMAGE = 256u,
    RAW_IMAGE_NOTIFY = 512u,
    PREVIEW_METADATA = 1024u,
};

/**
 * Information for a single detected face.
 */
struct CameraFace final {
    ::android::hardware::hidl_array<int32_t, 4> rect __attribute__ ((aligned(4)));
    int32_t score __attribute__ ((aligned(4)));
    int32_t id __attribute__ ((aligned(4)));
    ::android::hardware::hidl_array<int32_t, 2> leftEye __attribute__ ((aligned(4)));
    ::android::hardware::hidl_array<int32_t, 2> rightEye __attribute__ ((aligned(4)));
    ::android::hardware::hidl_array<int32_t, 2> mouth __attribute__ ((aligned(4)));
};

static_assert(offsetof(::android::hardware::camera::device::V1_0::CameraFace, rect) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V1_0::CameraFace, score) == 16, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V1_0::CameraFace, id) == 20, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V1_0::CameraFace, leftEye) == 24, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V1_0::CameraFace, rightEye) == 32, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V1_0::CameraFace, mouth) == 40, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V1_0::CameraFace) == 48, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V1_0::CameraFace) == 4, "wrong alignment");

/**
 * The metadata of the frame data, such as face detection result.
 */
struct CameraFrameMetadata final {
    ::android::hardware::hidl_vec<::android::hardware::camera::device::V1_0::CameraFace> faces __attribute__ ((aligned(8)));
};

static_assert(offsetof(::android::hardware::camera::device::V1_0::CameraFrameMetadata, faces) == 0, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V1_0::CameraFrameMetadata) == 16, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V1_0::CameraFrameMetadata) == 8, "wrong alignment");

/**
 * A simple integer handle to use to reference a particular memory buffer
 * between the HAL and the framework.
 */
typedef uint32_t MemoryId;

struct HandleTimestampMessage final {
    ::android::hardware::hidl_handle frameData __attribute__ ((aligned(8)));
    uint32_t data __attribute__ ((aligned(4)));
    uint32_t bufferIndex __attribute__ ((aligned(4)));
    int64_t timestamp __attribute__ ((aligned(8)));
};

static_assert(offsetof(::android::hardware::camera::device::V1_0::HandleTimestampMessage, frameData) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V1_0::HandleTimestampMessage, data) == 16, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V1_0::HandleTimestampMessage, bufferIndex) == 20, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V1_0::HandleTimestampMessage, timestamp) == 24, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V1_0::HandleTimestampMessage) == 32, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V1_0::HandleTimestampMessage) == 8, "wrong alignment");

struct VideoFrameMessage final {
    ::android::hardware::hidl_handle frameData __attribute__ ((aligned(8)));
    uint32_t data __attribute__ ((aligned(4)));
    uint32_t bufferIndex __attribute__ ((aligned(4)));
};

static_assert(offsetof(::android::hardware::camera::device::V1_0::VideoFrameMessage, frameData) == 0, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V1_0::VideoFrameMessage, data) == 16, "wrong offset");
static_assert(offsetof(::android::hardware::camera::device::V1_0::VideoFrameMessage, bufferIndex) == 20, "wrong offset");
static_assert(sizeof(::android::hardware::camera::device::V1_0::VideoFrameMessage) == 24, "wrong size");
static_assert(__alignof(::android::hardware::camera::device::V1_0::VideoFrameMessage) == 8, "wrong alignment");

constexpr uint32_t operator|(const ::android::hardware::camera::device::V1_0::CameraFacing lhs, const ::android::hardware::camera::device::V1_0::CameraFacing rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const uint32_t lhs, const ::android::hardware::camera::device::V1_0::CameraFacing rhs) {
    return static_cast<uint32_t>(lhs | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V1_0::CameraFacing lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | rhs);
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V1_0::CameraFacing lhs, const ::android::hardware::camera::device::V1_0::CameraFacing rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const uint32_t lhs, const ::android::hardware::camera::device::V1_0::CameraFacing rhs) {
    return static_cast<uint32_t>(lhs & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V1_0::CameraFacing lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & rhs);
}

constexpr uint32_t &operator|=(uint32_t& v, const ::android::hardware::camera::device::V1_0::CameraFacing e) {
    v |= static_cast<uint32_t>(e);
    return v;
}

constexpr uint32_t &operator&=(uint32_t& v, const ::android::hardware::camera::device::V1_0::CameraFacing e) {
    v &= static_cast<uint32_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint32_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V1_0::CameraFacing>(uint32_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V1_0::CameraFacing> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V1_0::CameraFacing::BACK) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::CameraFacing::BACK)) {
        os += (first ? "" : " | ");
        os += "BACK";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::CameraFacing::BACK;
    }
    if ((o & ::android::hardware::camera::device::V1_0::CameraFacing::FRONT) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::CameraFacing::FRONT)) {
        os += (first ? "" : " | ");
        os += "FRONT";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::CameraFacing::FRONT;
    }
    if ((o & ::android::hardware::camera::device::V1_0::CameraFacing::EXTERNAL) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::CameraFacing::EXTERNAL)) {
        os += (first ? "" : " | ");
        os += "EXTERNAL";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::CameraFacing::EXTERNAL;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V1_0::CameraFacing o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V1_0::CameraFacing::BACK) {
        return "BACK";
    }
    if (o == ::android::hardware::camera::device::V1_0::CameraFacing::FRONT) {
        return "FRONT";
    }
    if (o == ::android::hardware::camera::device::V1_0::CameraFacing::EXTERNAL) {
        return "EXTERNAL";
    }
    std::string os;
    os += toHexString(static_cast<uint32_t>(o));
    return os;
}

static inline std::string toString(const ::android::hardware::camera::device::V1_0::CameraInfo& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".facing = ";
    os += ::android::hardware::camera::device::V1_0::toString(o.facing);
    os += ", .orientation = ";
    os += ::android::hardware::toString(o.orientation);
    os += "}"; return os;
}

static inline bool operator==(const ::android::hardware::camera::device::V1_0::CameraInfo& lhs, const ::android::hardware::camera::device::V1_0::CameraInfo& rhs) {
    if (lhs.facing != rhs.facing) {
        return false;
    }
    if (lhs.orientation != rhs.orientation) {
        return false;
    }
    return true;
}

static inline bool operator!=(const ::android::hardware::camera::device::V1_0::CameraInfo& lhs,const ::android::hardware::camera::device::V1_0::CameraInfo& rhs){
    return !(lhs == rhs);
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V1_0::FrameCallbackFlag lhs, const ::android::hardware::camera::device::V1_0::FrameCallbackFlag rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const uint32_t lhs, const ::android::hardware::camera::device::V1_0::FrameCallbackFlag rhs) {
    return static_cast<uint32_t>(lhs | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V1_0::FrameCallbackFlag lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | rhs);
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V1_0::FrameCallbackFlag lhs, const ::android::hardware::camera::device::V1_0::FrameCallbackFlag rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const uint32_t lhs, const ::android::hardware::camera::device::V1_0::FrameCallbackFlag rhs) {
    return static_cast<uint32_t>(lhs & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V1_0::FrameCallbackFlag lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & rhs);
}

constexpr uint32_t &operator|=(uint32_t& v, const ::android::hardware::camera::device::V1_0::FrameCallbackFlag e) {
    v |= static_cast<uint32_t>(e);
    return v;
}

constexpr uint32_t &operator&=(uint32_t& v, const ::android::hardware::camera::device::V1_0::FrameCallbackFlag e) {
    v &= static_cast<uint32_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint32_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V1_0::FrameCallbackFlag>(uint32_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V1_0::FrameCallbackFlag> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V1_0::FrameCallbackFlag::ENABLE_MASK) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::FrameCallbackFlag::ENABLE_MASK)) {
        os += (first ? "" : " | ");
        os += "ENABLE_MASK";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::FrameCallbackFlag::ENABLE_MASK;
    }
    if ((o & ::android::hardware::camera::device::V1_0::FrameCallbackFlag::ONE_SHOT_MASK) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::FrameCallbackFlag::ONE_SHOT_MASK)) {
        os += (first ? "" : " | ");
        os += "ONE_SHOT_MASK";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::FrameCallbackFlag::ONE_SHOT_MASK;
    }
    if ((o & ::android::hardware::camera::device::V1_0::FrameCallbackFlag::COPY_OUT_MASK) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::FrameCallbackFlag::COPY_OUT_MASK)) {
        os += (first ? "" : " | ");
        os += "COPY_OUT_MASK";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::FrameCallbackFlag::COPY_OUT_MASK;
    }
    if ((o & ::android::hardware::camera::device::V1_0::FrameCallbackFlag::NOOP) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::FrameCallbackFlag::NOOP)) {
        os += (first ? "" : " | ");
        os += "NOOP";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::FrameCallbackFlag::NOOP;
    }
    if ((o & ::android::hardware::camera::device::V1_0::FrameCallbackFlag::CAMCORDER) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::FrameCallbackFlag::CAMCORDER)) {
        os += (first ? "" : " | ");
        os += "CAMCORDER";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::FrameCallbackFlag::CAMCORDER;
    }
    if ((o & ::android::hardware::camera::device::V1_0::FrameCallbackFlag::CAMERA) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::FrameCallbackFlag::CAMERA)) {
        os += (first ? "" : " | ");
        os += "CAMERA";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::FrameCallbackFlag::CAMERA;
    }
    if ((o & ::android::hardware::camera::device::V1_0::FrameCallbackFlag::BARCODE_SCANNER) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::FrameCallbackFlag::BARCODE_SCANNER)) {
        os += (first ? "" : " | ");
        os += "BARCODE_SCANNER";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::FrameCallbackFlag::BARCODE_SCANNER;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V1_0::FrameCallbackFlag o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V1_0::FrameCallbackFlag::ENABLE_MASK) {
        return "ENABLE_MASK";
    }
    if (o == ::android::hardware::camera::device::V1_0::FrameCallbackFlag::ONE_SHOT_MASK) {
        return "ONE_SHOT_MASK";
    }
    if (o == ::android::hardware::camera::device::V1_0::FrameCallbackFlag::COPY_OUT_MASK) {
        return "COPY_OUT_MASK";
    }
    if (o == ::android::hardware::camera::device::V1_0::FrameCallbackFlag::NOOP) {
        return "NOOP";
    }
    if (o == ::android::hardware::camera::device::V1_0::FrameCallbackFlag::CAMCORDER) {
        return "CAMCORDER";
    }
    if (o == ::android::hardware::camera::device::V1_0::FrameCallbackFlag::CAMERA) {
        return "CAMERA";
    }
    if (o == ::android::hardware::camera::device::V1_0::FrameCallbackFlag::BARCODE_SCANNER) {
        return "BARCODE_SCANNER";
    }
    std::string os;
    os += toHexString(static_cast<uint32_t>(o));
    return os;
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V1_0::CommandType lhs, const ::android::hardware::camera::device::V1_0::CommandType rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const uint32_t lhs, const ::android::hardware::camera::device::V1_0::CommandType rhs) {
    return static_cast<uint32_t>(lhs | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V1_0::CommandType lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | rhs);
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V1_0::CommandType lhs, const ::android::hardware::camera::device::V1_0::CommandType rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const uint32_t lhs, const ::android::hardware::camera::device::V1_0::CommandType rhs) {
    return static_cast<uint32_t>(lhs & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V1_0::CommandType lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & rhs);
}

constexpr uint32_t &operator|=(uint32_t& v, const ::android::hardware::camera::device::V1_0::CommandType e) {
    v |= static_cast<uint32_t>(e);
    return v;
}

constexpr uint32_t &operator&=(uint32_t& v, const ::android::hardware::camera::device::V1_0::CommandType e) {
    v &= static_cast<uint32_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint32_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V1_0::CommandType>(uint32_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V1_0::CommandType> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V1_0::CommandType::START_SMOOTH_ZOOM) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::CommandType::START_SMOOTH_ZOOM)) {
        os += (first ? "" : " | ");
        os += "START_SMOOTH_ZOOM";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::CommandType::START_SMOOTH_ZOOM;
    }
    if ((o & ::android::hardware::camera::device::V1_0::CommandType::STOP_SMOOTH_ZOOM) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::CommandType::STOP_SMOOTH_ZOOM)) {
        os += (first ? "" : " | ");
        os += "STOP_SMOOTH_ZOOM";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::CommandType::STOP_SMOOTH_ZOOM;
    }
    if ((o & ::android::hardware::camera::device::V1_0::CommandType::START_FACE_DETECTION) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::CommandType::START_FACE_DETECTION)) {
        os += (first ? "" : " | ");
        os += "START_FACE_DETECTION";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::CommandType::START_FACE_DETECTION;
    }
    if ((o & ::android::hardware::camera::device::V1_0::CommandType::STOP_FACE_DETECTION) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::CommandType::STOP_FACE_DETECTION)) {
        os += (first ? "" : " | ");
        os += "STOP_FACE_DETECTION";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::CommandType::STOP_FACE_DETECTION;
    }
    if ((o & ::android::hardware::camera::device::V1_0::CommandType::ENABLE_FOCUS_MOVE_MSG) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::CommandType::ENABLE_FOCUS_MOVE_MSG)) {
        os += (first ? "" : " | ");
        os += "ENABLE_FOCUS_MOVE_MSG";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::CommandType::ENABLE_FOCUS_MOVE_MSG;
    }
    if ((o & ::android::hardware::camera::device::V1_0::CommandType::SET_VIDEO_FORMAT) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::CommandType::SET_VIDEO_FORMAT)) {
        os += (first ? "" : " | ");
        os += "SET_VIDEO_FORMAT";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::CommandType::SET_VIDEO_FORMAT;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V1_0::CommandType o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V1_0::CommandType::START_SMOOTH_ZOOM) {
        return "START_SMOOTH_ZOOM";
    }
    if (o == ::android::hardware::camera::device::V1_0::CommandType::STOP_SMOOTH_ZOOM) {
        return "STOP_SMOOTH_ZOOM";
    }
    if (o == ::android::hardware::camera::device::V1_0::CommandType::START_FACE_DETECTION) {
        return "START_FACE_DETECTION";
    }
    if (o == ::android::hardware::camera::device::V1_0::CommandType::STOP_FACE_DETECTION) {
        return "STOP_FACE_DETECTION";
    }
    if (o == ::android::hardware::camera::device::V1_0::CommandType::ENABLE_FOCUS_MOVE_MSG) {
        return "ENABLE_FOCUS_MOVE_MSG";
    }
    if (o == ::android::hardware::camera::device::V1_0::CommandType::SET_VIDEO_FORMAT) {
        return "SET_VIDEO_FORMAT";
    }
    std::string os;
    os += toHexString(static_cast<uint32_t>(o));
    return os;
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg lhs, const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const uint32_t lhs, const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg rhs) {
    return static_cast<uint32_t>(lhs | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | rhs);
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg lhs, const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const uint32_t lhs, const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg rhs) {
    return static_cast<uint32_t>(lhs & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & rhs);
}

constexpr uint32_t &operator|=(uint32_t& v, const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg e) {
    v |= static_cast<uint32_t>(e);
    return v;
}

constexpr uint32_t &operator&=(uint32_t& v, const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg e) {
    v &= static_cast<uint32_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint32_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V1_0::NotifyCallbackMsg>(uint32_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V1_0::NotifyCallbackMsg> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::ERROR) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::NotifyCallbackMsg::ERROR)) {
        os += (first ? "" : " | ");
        os += "ERROR";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::ERROR;
    }
    if ((o & ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::SHUTTER) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::NotifyCallbackMsg::SHUTTER)) {
        os += (first ? "" : " | ");
        os += "SHUTTER";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::SHUTTER;
    }
    if ((o & ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::FOCUS) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::NotifyCallbackMsg::FOCUS)) {
        os += (first ? "" : " | ");
        os += "FOCUS";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::FOCUS;
    }
    if ((o & ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::ZOOM) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::NotifyCallbackMsg::ZOOM)) {
        os += (first ? "" : " | ");
        os += "ZOOM";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::ZOOM;
    }
    if ((o & ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::FOCUS_MOVE) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::NotifyCallbackMsg::FOCUS_MOVE)) {
        os += (first ? "" : " | ");
        os += "FOCUS_MOVE";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::FOCUS_MOVE;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V1_0::NotifyCallbackMsg o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::ERROR) {
        return "ERROR";
    }
    if (o == ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::SHUTTER) {
        return "SHUTTER";
    }
    if (o == ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::FOCUS) {
        return "FOCUS";
    }
    if (o == ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::ZOOM) {
        return "ZOOM";
    }
    if (o == ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::FOCUS_MOVE) {
        return "FOCUS_MOVE";
    }
    std::string os;
    os += toHexString(static_cast<uint32_t>(o));
    return os;
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V1_0::DataCallbackMsg lhs, const ::android::hardware::camera::device::V1_0::DataCallbackMsg rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const uint32_t lhs, const ::android::hardware::camera::device::V1_0::DataCallbackMsg rhs) {
    return static_cast<uint32_t>(lhs | static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator|(const ::android::hardware::camera::device::V1_0::DataCallbackMsg lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) | rhs);
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V1_0::DataCallbackMsg lhs, const ::android::hardware::camera::device::V1_0::DataCallbackMsg rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const uint32_t lhs, const ::android::hardware::camera::device::V1_0::DataCallbackMsg rhs) {
    return static_cast<uint32_t>(lhs & static_cast<uint32_t>(rhs));
}

constexpr uint32_t operator&(const ::android::hardware::camera::device::V1_0::DataCallbackMsg lhs, const uint32_t rhs) {
    return static_cast<uint32_t>(static_cast<uint32_t>(lhs) & rhs);
}

constexpr uint32_t &operator|=(uint32_t& v, const ::android::hardware::camera::device::V1_0::DataCallbackMsg e) {
    v |= static_cast<uint32_t>(e);
    return v;
}

constexpr uint32_t &operator&=(uint32_t& v, const ::android::hardware::camera::device::V1_0::DataCallbackMsg e) {
    v &= static_cast<uint32_t>(e);
    return v;
}

template<typename>
static inline std::string toString(uint32_t o);
template<>
inline std::string toString<::android::hardware::camera::device::V1_0::DataCallbackMsg>(uint32_t o) {
    using ::android::hardware::details::toHexString;
    std::string os;
    ::android::hardware::hidl_bitfield<::android::hardware::camera::device::V1_0::DataCallbackMsg> flipped = 0;
    bool first = true;
    if ((o & ::android::hardware::camera::device::V1_0::DataCallbackMsg::PREVIEW_FRAME) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::DataCallbackMsg::PREVIEW_FRAME)) {
        os += (first ? "" : " | ");
        os += "PREVIEW_FRAME";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::DataCallbackMsg::PREVIEW_FRAME;
    }
    if ((o & ::android::hardware::camera::device::V1_0::DataCallbackMsg::VIDEO_FRAME) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::DataCallbackMsg::VIDEO_FRAME)) {
        os += (first ? "" : " | ");
        os += "VIDEO_FRAME";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::DataCallbackMsg::VIDEO_FRAME;
    }
    if ((o & ::android::hardware::camera::device::V1_0::DataCallbackMsg::POSTVIEW_FRAME) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::DataCallbackMsg::POSTVIEW_FRAME)) {
        os += (first ? "" : " | ");
        os += "POSTVIEW_FRAME";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::DataCallbackMsg::POSTVIEW_FRAME;
    }
    if ((o & ::android::hardware::camera::device::V1_0::DataCallbackMsg::RAW_IMAGE) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::DataCallbackMsg::RAW_IMAGE)) {
        os += (first ? "" : " | ");
        os += "RAW_IMAGE";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::DataCallbackMsg::RAW_IMAGE;
    }
    if ((o & ::android::hardware::camera::device::V1_0::DataCallbackMsg::COMPRESSED_IMAGE) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::DataCallbackMsg::COMPRESSED_IMAGE)) {
        os += (first ? "" : " | ");
        os += "COMPRESSED_IMAGE";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::DataCallbackMsg::COMPRESSED_IMAGE;
    }
    if ((o & ::android::hardware::camera::device::V1_0::DataCallbackMsg::RAW_IMAGE_NOTIFY) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::DataCallbackMsg::RAW_IMAGE_NOTIFY)) {
        os += (first ? "" : " | ");
        os += "RAW_IMAGE_NOTIFY";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::DataCallbackMsg::RAW_IMAGE_NOTIFY;
    }
    if ((o & ::android::hardware::camera::device::V1_0::DataCallbackMsg::PREVIEW_METADATA) == static_cast<uint32_t>(::android::hardware::camera::device::V1_0::DataCallbackMsg::PREVIEW_METADATA)) {
        os += (first ? "" : " | ");
        os += "PREVIEW_METADATA";
        first = false;
        flipped |= ::android::hardware::camera::device::V1_0::DataCallbackMsg::PREVIEW_METADATA;
    }
    if (o != flipped) {
        os += (first ? "" : " | ");
        os += toHexString(o & (~flipped));
    }os += " (";
    os += toHexString(o);
    os += ")";
    return os;
}

static inline std::string toString(::android::hardware::camera::device::V1_0::DataCallbackMsg o) {
    using ::android::hardware::details::toHexString;
    if (o == ::android::hardware::camera::device::V1_0::DataCallbackMsg::PREVIEW_FRAME) {
        return "PREVIEW_FRAME";
    }
    if (o == ::android::hardware::camera::device::V1_0::DataCallbackMsg::VIDEO_FRAME) {
        return "VIDEO_FRAME";
    }
    if (o == ::android::hardware::camera::device::V1_0::DataCallbackMsg::POSTVIEW_FRAME) {
        return "POSTVIEW_FRAME";
    }
    if (o == ::android::hardware::camera::device::V1_0::DataCallbackMsg::RAW_IMAGE) {
        return "RAW_IMAGE";
    }
    if (o == ::android::hardware::camera::device::V1_0::DataCallbackMsg::COMPRESSED_IMAGE) {
        return "COMPRESSED_IMAGE";
    }
    if (o == ::android::hardware::camera::device::V1_0::DataCallbackMsg::RAW_IMAGE_NOTIFY) {
        return "RAW_IMAGE_NOTIFY";
    }
    if (o == ::android::hardware::camera::device::V1_0::DataCallbackMsg::PREVIEW_METADATA) {
        return "PREVIEW_METADATA";
    }
    std::string os;
    os += toHexString(static_cast<uint32_t>(o));
    return os;
}

static inline std::string toString(const ::android::hardware::camera::device::V1_0::CameraFace& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".rect = ";
    os += ::android::hardware::toString(o.rect);
    os += ", .score = ";
    os += ::android::hardware::toString(o.score);
    os += ", .id = ";
    os += ::android::hardware::toString(o.id);
    os += ", .leftEye = ";
    os += ::android::hardware::toString(o.leftEye);
    os += ", .rightEye = ";
    os += ::android::hardware::toString(o.rightEye);
    os += ", .mouth = ";
    os += ::android::hardware::toString(o.mouth);
    os += "}"; return os;
}

static inline bool operator==(const ::android::hardware::camera::device::V1_0::CameraFace& lhs, const ::android::hardware::camera::device::V1_0::CameraFace& rhs) {
    if (lhs.rect != rhs.rect) {
        return false;
    }
    if (lhs.score != rhs.score) {
        return false;
    }
    if (lhs.id != rhs.id) {
        return false;
    }
    if (lhs.leftEye != rhs.leftEye) {
        return false;
    }
    if (lhs.rightEye != rhs.rightEye) {
        return false;
    }
    if (lhs.mouth != rhs.mouth) {
        return false;
    }
    return true;
}

static inline bool operator!=(const ::android::hardware::camera::device::V1_0::CameraFace& lhs,const ::android::hardware::camera::device::V1_0::CameraFace& rhs){
    return !(lhs == rhs);
}

static inline std::string toString(const ::android::hardware::camera::device::V1_0::CameraFrameMetadata& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".faces = ";
    os += ::android::hardware::toString(o.faces);
    os += "}"; return os;
}

static inline bool operator==(const ::android::hardware::camera::device::V1_0::CameraFrameMetadata& lhs, const ::android::hardware::camera::device::V1_0::CameraFrameMetadata& rhs) {
    if (lhs.faces != rhs.faces) {
        return false;
    }
    return true;
}

static inline bool operator!=(const ::android::hardware::camera::device::V1_0::CameraFrameMetadata& lhs,const ::android::hardware::camera::device::V1_0::CameraFrameMetadata& rhs){
    return !(lhs == rhs);
}

static inline std::string toString(const ::android::hardware::camera::device::V1_0::HandleTimestampMessage& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".frameData = ";
    os += ::android::hardware::toString(o.frameData);
    os += ", .data = ";
    os += ::android::hardware::toString(o.data);
    os += ", .bufferIndex = ";
    os += ::android::hardware::toString(o.bufferIndex);
    os += ", .timestamp = ";
    os += ::android::hardware::toString(o.timestamp);
    os += "}"; return os;
}

// operator== and operator!= are not generated for HandleTimestampMessage

static inline std::string toString(const ::android::hardware::camera::device::V1_0::VideoFrameMessage& o) {
    using ::android::hardware::toString;
    std::string os;
    os += "{";
    os += ".frameData = ";
    os += ::android::hardware::toString(o.frameData);
    os += ", .data = ";
    os += ::android::hardware::toString(o.data);
    os += ", .bufferIndex = ";
    os += ::android::hardware::toString(o.bufferIndex);
    os += "}"; return os;
}

// operator== and operator!= are not generated for VideoFrameMessage


}  // namespace V1_0
}  // namespace device
}  // namespace camera
}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V1_0::CameraFacing>
{
    const ::android::hardware::camera::device::V1_0::CameraFacing* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V1_0::CameraFacing* end() { return begin() + 3; }
    private:
    static const ::android::hardware::camera::device::V1_0::CameraFacing* static_begin() {
        static const ::android::hardware::camera::device::V1_0::CameraFacing kVals[3] {
            ::android::hardware::camera::device::V1_0::CameraFacing::BACK,
            ::android::hardware::camera::device::V1_0::CameraFacing::FRONT,
            ::android::hardware::camera::device::V1_0::CameraFacing::EXTERNAL,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V1_0::FrameCallbackFlag>
{
    const ::android::hardware::camera::device::V1_0::FrameCallbackFlag* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V1_0::FrameCallbackFlag* end() { return begin() + 7; }
    private:
    static const ::android::hardware::camera::device::V1_0::FrameCallbackFlag* static_begin() {
        static const ::android::hardware::camera::device::V1_0::FrameCallbackFlag kVals[7] {
            ::android::hardware::camera::device::V1_0::FrameCallbackFlag::ENABLE_MASK,
            ::android::hardware::camera::device::V1_0::FrameCallbackFlag::ONE_SHOT_MASK,
            ::android::hardware::camera::device::V1_0::FrameCallbackFlag::COPY_OUT_MASK,
            ::android::hardware::camera::device::V1_0::FrameCallbackFlag::NOOP,
            ::android::hardware::camera::device::V1_0::FrameCallbackFlag::CAMCORDER,
            ::android::hardware::camera::device::V1_0::FrameCallbackFlag::CAMERA,
            ::android::hardware::camera::device::V1_0::FrameCallbackFlag::BARCODE_SCANNER,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V1_0::CommandType>
{
    const ::android::hardware::camera::device::V1_0::CommandType* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V1_0::CommandType* end() { return begin() + 6; }
    private:
    static const ::android::hardware::camera::device::V1_0::CommandType* static_begin() {
        static const ::android::hardware::camera::device::V1_0::CommandType kVals[6] {
            ::android::hardware::camera::device::V1_0::CommandType::START_SMOOTH_ZOOM,
            ::android::hardware::camera::device::V1_0::CommandType::STOP_SMOOTH_ZOOM,
            ::android::hardware::camera::device::V1_0::CommandType::START_FACE_DETECTION,
            ::android::hardware::camera::device::V1_0::CommandType::STOP_FACE_DETECTION,
            ::android::hardware::camera::device::V1_0::CommandType::ENABLE_FOCUS_MOVE_MSG,
            ::android::hardware::camera::device::V1_0::CommandType::SET_VIDEO_FORMAT,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V1_0::NotifyCallbackMsg>
{
    const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg* end() { return begin() + 5; }
    private:
    static const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg* static_begin() {
        static const ::android::hardware::camera::device::V1_0::NotifyCallbackMsg kVals[5] {
            ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::ERROR,
            ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::SHUTTER,
            ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::FOCUS,
            ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::ZOOM,
            ::android::hardware::camera::device::V1_0::NotifyCallbackMsg::FOCUS_MOVE,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android
namespace android {
namespace hardware {
template<> struct hidl_enum_iterator<::android::hardware::camera::device::V1_0::DataCallbackMsg>
{
    const ::android::hardware::camera::device::V1_0::DataCallbackMsg* begin() { return static_begin(); }
    const ::android::hardware::camera::device::V1_0::DataCallbackMsg* end() { return begin() + 7; }
    private:
    static const ::android::hardware::camera::device::V1_0::DataCallbackMsg* static_begin() {
        static const ::android::hardware::camera::device::V1_0::DataCallbackMsg kVals[7] {
            ::android::hardware::camera::device::V1_0::DataCallbackMsg::PREVIEW_FRAME,
            ::android::hardware::camera::device::V1_0::DataCallbackMsg::VIDEO_FRAME,
            ::android::hardware::camera::device::V1_0::DataCallbackMsg::POSTVIEW_FRAME,
            ::android::hardware::camera::device::V1_0::DataCallbackMsg::RAW_IMAGE,
            ::android::hardware::camera::device::V1_0::DataCallbackMsg::COMPRESSED_IMAGE,
            ::android::hardware::camera::device::V1_0::DataCallbackMsg::RAW_IMAGE_NOTIFY,
            ::android::hardware::camera::device::V1_0::DataCallbackMsg::PREVIEW_METADATA,
        };
        return &kVals[0];
    }};

}  // namespace hardware
}  // namespace android

#endif  // HIDL_GENERATED_ANDROID_HARDWARE_CAMERA_DEVICE_V1_0_TYPES_H
