#ifndef HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_PROVIDER_V1_0_IVENDORSOMCCAMERAPROVIDER_H
#define HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_PROVIDER_V1_0_IVENDORSOMCCAMERAPROVIDER_H

#include <android/hardware/camera/common/1.0/types.h>
#include <android/hardware/camera/provider/2.4/ICameraProvider.h>
#include <vendor/somc/hardware/camera/cacao/1.0/ICacao.h>
#include <vendor/somc/hardware/camera/cacao/2.0/ICacao.h>
#include <vendor/somc/hardware/camera/cacao/3.0/ICacao.h>
#include <vendor/somc/hardware/camera/device/1.0/ICameraExtensionDevice.h>

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
namespace provider {
namespace V1_0 {

struct IVendorSomcCameraProvider : public ::android::hardware::camera::provider::V2_4::ICameraProvider {
    typedef android::hardware::details::i_tag _hidl_tag;

    // Forward declaration for forward reference support:

    virtual bool isRemote() const override { return false; }


    /**
     * setCallback:
     * 
     * Provide a callback interface to the HAL provider to inform framework of
     * asynchronous camera events. The framework must call this function once
     * during camera service startup, before any other calls to the provider
     * (note that in case the camera service restarts, this method must be
     * invoked again during its startup).
     * 
     * @param callback
     *     A non-null callback interface to invoke when camera events occur.
     * @return status
     *     Status code for the operation, one of:
     *     OK:
     *         On success
     *     INTERNAL_ERROR:
     *         An unexpected internal error occurred while setting the callbacks
     *     ILLEGAL_ARGUMENT:
     *         The callback argument is invalid (for example, null).
     * 
     */
    virtual ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> setCallback(const ::android::sp<::android::hardware::camera::provider::V2_4::ICameraProviderCallback>& callback) = 0;

    using getVendorTags_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, const ::android::hardware::hidl_vec<::android::hardware::camera::common::V1_0::VendorTagSection>& sections)>;
    /**
     * getVendorTags:
     * 
     * Retrieve all vendor tags supported by devices discoverable through this
     * provider. The tags are grouped into sections.
     * 
     * @return status
     *     Status code for the operation, one of:
     *     OK:
     *         On success
     *     INTERNAL_ERROR:
     *         An unexpected internal error occurred while setting the callbacks
     * @return sections
     *     The supported vendor tag sections; empty if there are no supported
     *     vendor tags, or status is not OK.
     * 
     */
    virtual ::android::hardware::Return<void> getVendorTags(getVendorTags_cb _hidl_cb) = 0;

    using getCameraIdList_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, const ::android::hardware::hidl_vec<::android::hardware::hidl_string>& cameraDeviceNames)>;
    /**
     * getCameraIdList:
     * 
     * Returns the list of internal camera device interfaces known to this
     * camera provider. These devices can then be accessed via the hardware
     * service manager.
     * 
     * External camera devices (camera facing EXTERNAL) must be reported through
     * the device status change callback, not in this list. Only devices with
     * facing BACK or FRONT must be listed here.
     * 
     * @return status Status code for the operation, one of:
     *     OK:
     *         On a succesful generation of camera ID list
     *     INTERNAL_ERROR:
     *         A camera ID list cannot be created. This may be due to
     *         a failure to initialize the camera subsystem, for example.
     * @return cameraDeviceNames The vector of internal camera device
     *     names known to this provider.
     */
    virtual ::android::hardware::Return<void> getCameraIdList(getCameraIdList_cb _hidl_cb) = 0;

    using isSetTorchModeSupported_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, bool support)>;
    /**
     * isSetTorchModeSupported:
     * 
     * Returns if the camera devices known to this camera provider support
     * setTorchMode API or not. If the provider does not support setTorchMode
     * API, calling to setTorchMode will return METHOD_NOT_SUPPORTED.
     * 
     * Note that not every camera device has a flash unit, so even this API
     * returns true, setTorchMode call might still fail due to the camera device
     * does not have a flash unit. In such case, the returned status will be
     * OPERATION_NOT_SUPPORTED.
     * 
     * @return status Status code for the operation, one of:
     *     OK:
     *         On a succesful call
     *     INTERNAL_ERROR:
     *         Torch API support cannot be queried. This may be due to
     *         a failure to initialize the camera subsystem, for example.
     * @return support Whether the camera devices known to this provider
     *     supports setTorchMode API or not. Devices launched with SDK
     *     level 29 or higher must return true.
     * 
     */
    virtual ::android::hardware::Return<void> isSetTorchModeSupported(isSetTorchModeSupported_cb _hidl_cb) = 0;

    using getCameraDeviceInterface_V1_x_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, const ::android::sp<::android::hardware::camera::device::V1_0::ICameraDevice>& device)>;
    /**
     * getCameraDeviceInterface_VN_x:
     * 
     * Return a android.hardware.camera.device@N.x/ICameraDevice interface for
     * the requested device name. This does not power on the camera device, but
     * simply acquires the interface for querying the device static information,
     * or to additionally open the device for active use.
     * 
     * A separate method is required for each major revision of the camera device
     * HAL interface, since they are not compatible with each other.
     * 
     * Valid device names for this provider can be obtained via either
     * getCameraIdList(), or via availability callbacks from
     * ICameraProviderCallback::cameraDeviceStatusChange().
     * 
     * The returned interface must be of the highest defined minor version for
     * the major version; it's the responsibility of the HAL client to ensure
     * they do not use methods/etc that are not valid for the actual minor
     * version of the device.
     * 
     * @param cameraDeviceName the name of the device to get an interface to.
     * @return status Status code for the operation, one of:
     *     OK:
     *         On a succesful generation of camera ID list
     *     ILLEGAL_ARGUMENT:
     *         This device name is unknown, or has been disconnected
     *     OPERATION_NOT_SUPPORTED:
     *         The specified device does not support this major version of the
     *         HAL interface.
     *     INTERNAL_ERROR:
     *         A camera interface cannot be returned due to an unexpected
     *         internal error.
     * @return device The inteface to this camera device, or null in case of
     *     error.
     */
    virtual ::android::hardware::Return<void> getCameraDeviceInterface_V1_x(const ::android::hardware::hidl_string& cameraDeviceName, getCameraDeviceInterface_V1_x_cb _hidl_cb) = 0;

    using getCameraDeviceInterface_V3_x_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, const ::android::sp<::android::hardware::camera::device::V3_2::ICameraDevice>& device)>;
    virtual ::android::hardware::Return<void> getCameraDeviceInterface_V3_x(const ::android::hardware::hidl_string& cameraDeviceName, getCameraDeviceInterface_V3_x_cb _hidl_cb) = 0;

    using getCameraExtensionDeviceInterface_V1_0_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, const ::android::sp<::vendor::somc::hardware::camera::device::V1_0::ICameraExtensionDevice>& device)>;
    virtual ::android::hardware::Return<void> getCameraExtensionDeviceInterface_V1_0(const ::android::hardware::hidl_string& cameraDeviceName, getCameraExtensionDeviceInterface_V1_0_cb _hidl_cb) = 0;

    using getCacaoInterface_V1_0_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, const ::android::sp<::vendor::somc::hardware::camera::cacao::V1_0::ICacao>& service)>;
    virtual ::android::hardware::Return<void> getCacaoInterface_V1_0(getCacaoInterface_V1_0_cb _hidl_cb) = 0;

    using getCacaoInterface_V2_0_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, const ::android::sp<::vendor::somc::hardware::camera::cacao::V2_0::ICacao>& service)>;
    virtual ::android::hardware::Return<void> getCacaoInterface_V2_0(getCacaoInterface_V2_0_cb _hidl_cb) = 0;

    using getCacaoInterface_V3_0_cb = std::function<void(::android::hardware::camera::common::V1_0::Status status, const ::android::sp<::vendor::somc::hardware::camera::cacao::V3_0::ICacao>& service)>;
    virtual ::android::hardware::Return<void> getCacaoInterface_V3_0(getCacaoInterface_V3_0_cb _hidl_cb) = 0;

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
    static ::android::hardware::Return<::android::sp<::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider>> castFrom(const ::android::sp<::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider>& parent, bool emitError = false);
    static ::android::hardware::Return<::android::sp<::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider>> castFrom(const ::android::sp<::android::hardware::camera::provider::V2_4::ICameraProvider>& parent, bool emitError = false);
    static ::android::hardware::Return<::android::sp<::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider>> castFrom(const ::android::sp<::android::hidl::base::V1_0::IBase>& parent, bool emitError = false);

    static const char* descriptor;

    static ::android::sp<IVendorSomcCameraProvider> tryGetService(const std::string &serviceName="default", bool getStub=false);
    static ::android::sp<IVendorSomcCameraProvider> tryGetService(const char serviceName[], bool getStub=false)  { std::string str(serviceName ? serviceName : "");      return tryGetService(str, getStub); }
    static ::android::sp<IVendorSomcCameraProvider> tryGetService(const ::android::hardware::hidl_string& serviceName, bool getStub=false)  { std::string str(serviceName.c_str());      return tryGetService(str, getStub); }
    static ::android::sp<IVendorSomcCameraProvider> tryGetService(bool getStub) { return tryGetService("default", getStub); }
    static ::android::sp<IVendorSomcCameraProvider> getService(const std::string &serviceName="default", bool getStub=false);
    static ::android::sp<IVendorSomcCameraProvider> getService(const char serviceName[], bool getStub=false)  { std::string str(serviceName ? serviceName : "");      return getService(str, getStub); }
    static ::android::sp<IVendorSomcCameraProvider> getService(const ::android::hardware::hidl_string& serviceName, bool getStub=false)  { std::string str(serviceName.c_str());      return getService(str, getStub); }
    static ::android::sp<IVendorSomcCameraProvider> getService(bool getStub) { return getService("default", getStub); }
    __attribute__ ((warn_unused_result))::android::status_t registerAsService(const std::string &serviceName="default");
    static bool registerForNotifications(
            const std::string &serviceName,
            const ::android::sp<::android::hidl::manager::V1_0::IServiceNotification> &notification);
};

static inline std::string toString(const ::android::sp<::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider>& o) {
    std::string os = "[class or subclass of ";
    os += ::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider::descriptor;
    os += "]";
    os += o->isRemote() ? "@remote" : "@local";
    return os;
}


}  // namespace V1_0
}  // namespace provider
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor

#endif  // HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_PROVIDER_V1_0_IVENDORSOMCCAMERAPROVIDER_H
