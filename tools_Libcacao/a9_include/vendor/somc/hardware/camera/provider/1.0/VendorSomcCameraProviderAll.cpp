#define LOG_TAG "vendor.somc.hardware.camera.provider@1.0::VendorSomcCameraProvider"

#include <android/log.h>
#include <cutils/trace.h>
#include <hidl/HidlTransportSupport.h>

#include <android/hidl/manager/1.0/IServiceManager.h>
#include <vendor/somc/hardware/camera/provider/1.0/BpHwVendorSomcCameraProvider.h>
#include <vendor/somc/hardware/camera/provider/1.0/BnHwVendorSomcCameraProvider.h>
#include <vendor/somc/hardware/camera/provider/1.0/BsVendorSomcCameraProvider.h>
#include <android/hardware/camera/provider/2.4/BpHwCameraProvider.h>
#include <android/hidl/base/1.0/BpHwBase.h>
#include <hidl/ServiceManagement.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace provider {
namespace V1_0 {

const char* IVendorSomcCameraProvider::descriptor("vendor.somc.hardware.camera.provider@1.0::IVendorSomcCameraProvider");

__attribute__((constructor)) static void static_constructor() {
    ::android::hardware::details::getBnConstructorMap().set(IVendorSomcCameraProvider::descriptor,
            [](void *iIntf) -> ::android::sp<::android::hardware::IBinder> {
                return new BnHwVendorSomcCameraProvider(static_cast<IVendorSomcCameraProvider *>(iIntf));
            });
    ::android::hardware::details::getBsConstructorMap().set(IVendorSomcCameraProvider::descriptor,
            [](void *iIntf) -> ::android::sp<::android::hidl::base::V1_0::IBase> {
                return new BsVendorSomcCameraProvider(static_cast<IVendorSomcCameraProvider *>(iIntf));
            });
};

__attribute__((destructor))static void static_destructor() {
    ::android::hardware::details::getBnConstructorMap().erase(IVendorSomcCameraProvider::descriptor);
    ::android::hardware::details::getBsConstructorMap().erase(IVendorSomcCameraProvider::descriptor);
};

// Methods from ::android::hardware::camera::provider::V2_4::ICameraProvider follow.
// no default implementation for: ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> IVendorSomcCameraProvider::setCallback(const ::android::sp<::android::hardware::camera::provider::V2_4::ICameraProviderCallback>& callback)
// no default implementation for: ::android::hardware::Return<void> IVendorSomcCameraProvider::getVendorTags(getVendorTags_cb _hidl_cb)
// no default implementation for: ::android::hardware::Return<void> IVendorSomcCameraProvider::getCameraIdList(getCameraIdList_cb _hidl_cb)
// no default implementation for: ::android::hardware::Return<void> IVendorSomcCameraProvider::isSetTorchModeSupported(isSetTorchModeSupported_cb _hidl_cb)
// no default implementation for: ::android::hardware::Return<void> IVendorSomcCameraProvider::getCameraDeviceInterface_V1_x(const ::android::hardware::hidl_string& cameraDeviceName, getCameraDeviceInterface_V1_x_cb _hidl_cb)
// no default implementation for: ::android::hardware::Return<void> IVendorSomcCameraProvider::getCameraDeviceInterface_V3_x(const ::android::hardware::hidl_string& cameraDeviceName, getCameraDeviceInterface_V3_x_cb _hidl_cb)

// Methods from ::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider follow.
// no default implementation for: ::android::hardware::Return<void> IVendorSomcCameraProvider::getCameraExtensionDeviceInterface_V1_0(const ::android::hardware::hidl_string& cameraDeviceName, getCameraExtensionDeviceInterface_V1_0_cb _hidl_cb)
// no default implementation for: ::android::hardware::Return<void> IVendorSomcCameraProvider::getCacaoInterface_V1_0(getCacaoInterface_V1_0_cb _hidl_cb)
// no default implementation for: ::android::hardware::Return<void> IVendorSomcCameraProvider::getCacaoInterface_V2_0(getCacaoInterface_V2_0_cb _hidl_cb)
// no default implementation for: ::android::hardware::Return<void> IVendorSomcCameraProvider::getCacaoInterface_V3_0(getCacaoInterface_V3_0_cb _hidl_cb)

// Methods from ::android::hidl::base::V1_0::IBase follow.
::android::hardware::Return<void> IVendorSomcCameraProvider::interfaceChain(interfaceChain_cb _hidl_cb){
    _hidl_cb({
        ::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider::descriptor,
        ::android::hardware::camera::provider::V2_4::ICameraProvider::descriptor,
        ::android::hidl::base::V1_0::IBase::descriptor,
    });
    return ::android::hardware::Void();}

::android::hardware::Return<void> IVendorSomcCameraProvider::debug(const ::android::hardware::hidl_handle& fd, const ::android::hardware::hidl_vec<::android::hardware::hidl_string>& options){
    (void)fd;
    (void)options;
    return ::android::hardware::Void();}

::android::hardware::Return<void> IVendorSomcCameraProvider::interfaceDescriptor(interfaceDescriptor_cb _hidl_cb){
    _hidl_cb(::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider::descriptor);
    return ::android::hardware::Void();}

::android::hardware::Return<void> IVendorSomcCameraProvider::getHashChain(getHashChain_cb _hidl_cb){
    _hidl_cb({
        (uint8_t[32]){0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0} /* 0000000000000000000000000000000000000000000000000000000000000000 */,
        (uint8_t[32]){188,238,232,30,193,181,147,36,171,208,89,50,181,98,15,218,90,101,137,89,124,156,179,149,59,167,243,234,2,204,205,62} /* bceee81ec1b59324abd05932b5620fda5a6589597c9cb3953ba7f3ea02cccd3e */,
        (uint8_t[32]){189,218,182,24,77,122,52,109,166,160,125,192,130,140,241,154,105,111,76,170,54,17,197,31,46,20,86,90,20,180,15,217} /* bddab6184d7a346da6a07dc0828cf19a696f4caa3611c51f2e14565a14b40fd9 */});
    return ::android::hardware::Void();
}

::android::hardware::Return<void> IVendorSomcCameraProvider::setHALInstrumentation(){
    return ::android::hardware::Void();
}

::android::hardware::Return<bool> IVendorSomcCameraProvider::linkToDeath(const ::android::sp<::android::hardware::hidl_death_recipient>& recipient, uint64_t cookie){
    (void)cookie;
    return (recipient != nullptr);
}

::android::hardware::Return<void> IVendorSomcCameraProvider::ping(){
    return ::android::hardware::Void();
}

::android::hardware::Return<void> IVendorSomcCameraProvider::getDebugInfo(getDebugInfo_cb _hidl_cb){
    ::android::hidl::base::V1_0::DebugInfo info = {};
    info.pid = -1;
    info.ptr = 0;
    info.arch = 
    #if defined(__LP64__)
    ::android::hidl::base::V1_0::DebugInfo::Architecture::IS_64BIT
    #else
    ::android::hidl::base::V1_0::DebugInfo::Architecture::IS_32BIT
    #endif
    ;
    _hidl_cb(info);
    return ::android::hardware::Void();
}

::android::hardware::Return<void> IVendorSomcCameraProvider::notifySyspropsChanged(){
    ::android::report_sysprop_change();
    return ::android::hardware::Void();}

::android::hardware::Return<bool> IVendorSomcCameraProvider::unlinkToDeath(const ::android::sp<::android::hardware::hidl_death_recipient>& recipient){
    return (recipient != nullptr);
}


// static 
::android::hardware::Return<::android::sp<::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider>> IVendorSomcCameraProvider::castFrom(const ::android::sp<::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider>& parent, bool /* emitError */) {
    return parent;
}

// static 
::android::hardware::Return<::android::sp<::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider>> IVendorSomcCameraProvider::castFrom(const ::android::sp<::android::hardware::camera::provider::V2_4::ICameraProvider>& parent, bool emitError) {
    return ::android::hardware::details::castInterface<IVendorSomcCameraProvider, ::android::hardware::camera::provider::V2_4::ICameraProvider, BpHwVendorSomcCameraProvider>(
            parent, "vendor.somc.hardware.camera.provider@1.0::IVendorSomcCameraProvider", emitError);
}

// static 
::android::hardware::Return<::android::sp<::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider>> IVendorSomcCameraProvider::castFrom(const ::android::sp<::android::hidl::base::V1_0::IBase>& parent, bool emitError) {
    return ::android::hardware::details::castInterface<IVendorSomcCameraProvider, ::android::hidl::base::V1_0::IBase, BpHwVendorSomcCameraProvider>(
            parent, "vendor.somc.hardware.camera.provider@1.0::IVendorSomcCameraProvider", emitError);
}

BpHwVendorSomcCameraProvider::BpHwVendorSomcCameraProvider(const ::android::sp<::android::hardware::IBinder> &_hidl_impl)
        : BpInterface<IVendorSomcCameraProvider>(_hidl_impl),
          ::android::hardware::details::HidlInstrumentor("vendor.somc.hardware.camera.provider@1.0", "IVendorSomcCameraProvider") {
}

// Methods from ::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider follow.
::android::hardware::Return<void> BpHwVendorSomcCameraProvider::_hidl_getCameraExtensionDeviceInterface_V1_0(::android::hardware::IInterface *_hidl_this, ::android::hardware::details::HidlInstrumentor *_hidl_this_instrumentor, const ::android::hardware::hidl_string& cameraDeviceName, getCameraExtensionDeviceInterface_V1_0_cb _hidl_cb) {
    #ifdef __ANDROID_DEBUGGABLE__
    bool mEnableInstrumentation = _hidl_this_instrumentor->isInstrumentationEnabled();
    const auto &mInstrumentationCallbacks = _hidl_this_instrumentor->getInstrumentationCallbacks();
    #else
    (void) _hidl_this_instrumentor;
    #endif // __ANDROID_DEBUGGABLE__
    if (_hidl_cb == nullptr) {
        return ::android::hardware::Status::fromExceptionCode(
                ::android::hardware::Status::EX_ILLEGAL_ARGUMENT,
                "Null synchronous callback passed.");
    }

    atrace_begin(ATRACE_TAG_HAL, "HIDL::IVendorSomcCameraProvider::getCameraExtensionDeviceInterface_V1_0::client");
    #ifdef __ANDROID_DEBUGGABLE__
    if (UNLIKELY(mEnableInstrumentation)) {
        std::vector<void *> _hidl_args;
        _hidl_args.push_back((void *)&cameraDeviceName);
        for (const auto &callback: mInstrumentationCallbacks) {
            callback(InstrumentationEvent::CLIENT_API_ENTRY, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCameraExtensionDeviceInterface_V1_0", &_hidl_args);
        }
    }
    #endif // __ANDROID_DEBUGGABLE__

    ::android::hardware::Parcel _hidl_data;
    ::android::hardware::Parcel _hidl_reply;
    ::android::status_t _hidl_err;
    ::android::hardware::Status _hidl_status;

    ::android::hardware::camera::common::V1_0::Status _hidl_out_status;
    ::android::sp<::vendor::somc::hardware::camera::device::V1_0::ICameraExtensionDevice> _hidl_out_device;

    _hidl_err = _hidl_data.writeInterfaceToken(BpHwVendorSomcCameraProvider::descriptor);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    size_t _hidl_cameraDeviceName_parent;

    _hidl_err = _hidl_data.writeBuffer(&cameraDeviceName, sizeof(cameraDeviceName), &_hidl_cameraDeviceName_parent);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    _hidl_err = ::android::hardware::writeEmbeddedToParcel(
            cameraDeviceName,
            &_hidl_data,
            _hidl_cameraDeviceName_parent,
            0 /* parentOffset */);

    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    _hidl_err = ::android::hardware::IInterface::asBinder(_hidl_this)->transact(7 /* getCameraExtensionDeviceInterface_V1_0 */, _hidl_data, &_hidl_reply);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    _hidl_err = ::android::hardware::readFromParcel(&_hidl_status, _hidl_reply);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    if (!_hidl_status.isOk()) { return _hidl_status; }

    _hidl_err = _hidl_reply.readUint32((uint32_t *)&_hidl_out_status);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    {
        ::android::sp<::android::hardware::IBinder> _hidl_binder;
        _hidl_err = _hidl_reply.readNullableStrongBinder(&_hidl_binder);
        if (_hidl_err != ::android::OK) { goto _hidl_error; }

        _hidl_out_device = ::android::hardware::fromBinder<::vendor::somc::hardware::camera::device::V1_0::ICameraExtensionDevice,::vendor::somc::hardware::camera::device::V1_0::BpHwCameraExtensionDevice,::vendor::somc::hardware::camera::device::V1_0::BnHwCameraExtensionDevice>(_hidl_binder);
    }

    _hidl_cb(_hidl_out_status, _hidl_out_device);

    atrace_end(ATRACE_TAG_HAL);
    #ifdef __ANDROID_DEBUGGABLE__
    if (UNLIKELY(mEnableInstrumentation)) {
        std::vector<void *> _hidl_args;
        _hidl_args.push_back((void *)&_hidl_out_status);
        _hidl_args.push_back((void *)&_hidl_out_device);
        for (const auto &callback: mInstrumentationCallbacks) {
            callback(InstrumentationEvent::CLIENT_API_EXIT, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCameraExtensionDeviceInterface_V1_0", &_hidl_args);
        }
    }
    #endif // __ANDROID_DEBUGGABLE__

    _hidl_status.setFromStatusT(_hidl_err);
    return ::android::hardware::Return<void>();

_hidl_error:
    _hidl_status.setFromStatusT(_hidl_err);
    return ::android::hardware::Return<void>(_hidl_status);
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::_hidl_getCacaoInterface_V1_0(::android::hardware::IInterface *_hidl_this, ::android::hardware::details::HidlInstrumentor *_hidl_this_instrumentor, getCacaoInterface_V1_0_cb _hidl_cb) {
    #ifdef __ANDROID_DEBUGGABLE__
    bool mEnableInstrumentation = _hidl_this_instrumentor->isInstrumentationEnabled();
    const auto &mInstrumentationCallbacks = _hidl_this_instrumentor->getInstrumentationCallbacks();
    #else
    (void) _hidl_this_instrumentor;
    #endif // __ANDROID_DEBUGGABLE__
    if (_hidl_cb == nullptr) {
        return ::android::hardware::Status::fromExceptionCode(
                ::android::hardware::Status::EX_ILLEGAL_ARGUMENT,
                "Null synchronous callback passed.");
    }

    atrace_begin(ATRACE_TAG_HAL, "HIDL::IVendorSomcCameraProvider::getCacaoInterface_V1_0::client");
    #ifdef __ANDROID_DEBUGGABLE__
    if (UNLIKELY(mEnableInstrumentation)) {
        std::vector<void *> _hidl_args;
        for (const auto &callback: mInstrumentationCallbacks) {
            callback(InstrumentationEvent::CLIENT_API_ENTRY, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCacaoInterface_V1_0", &_hidl_args);
        }
    }
    #endif // __ANDROID_DEBUGGABLE__

    ::android::hardware::Parcel _hidl_data;
    ::android::hardware::Parcel _hidl_reply;
    ::android::status_t _hidl_err;
    ::android::hardware::Status _hidl_status;

    ::android::hardware::camera::common::V1_0::Status _hidl_out_status;
    ::android::sp<::vendor::somc::hardware::camera::cacao::V1_0::ICacao> _hidl_out_service;

    _hidl_err = _hidl_data.writeInterfaceToken(BpHwVendorSomcCameraProvider::descriptor);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    _hidl_err = ::android::hardware::IInterface::asBinder(_hidl_this)->transact(8 /* getCacaoInterface_V1_0 */, _hidl_data, &_hidl_reply);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    _hidl_err = ::android::hardware::readFromParcel(&_hidl_status, _hidl_reply);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    if (!_hidl_status.isOk()) { return _hidl_status; }

    _hidl_err = _hidl_reply.readUint32((uint32_t *)&_hidl_out_status);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    {
        ::android::sp<::android::hardware::IBinder> _hidl_binder;
        _hidl_err = _hidl_reply.readNullableStrongBinder(&_hidl_binder);
        if (_hidl_err != ::android::OK) { goto _hidl_error; }

        _hidl_out_service = ::android::hardware::fromBinder<::vendor::somc::hardware::camera::cacao::V1_0::ICacao,::vendor::somc::hardware::camera::cacao::V1_0::BpHwCacao,::vendor::somc::hardware::camera::cacao::V1_0::BnHwCacao>(_hidl_binder);
    }

    _hidl_cb(_hidl_out_status, _hidl_out_service);

    atrace_end(ATRACE_TAG_HAL);
    #ifdef __ANDROID_DEBUGGABLE__
    if (UNLIKELY(mEnableInstrumentation)) {
        std::vector<void *> _hidl_args;
        _hidl_args.push_back((void *)&_hidl_out_status);
        _hidl_args.push_back((void *)&_hidl_out_service);
        for (const auto &callback: mInstrumentationCallbacks) {
            callback(InstrumentationEvent::CLIENT_API_EXIT, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCacaoInterface_V1_0", &_hidl_args);
        }
    }
    #endif // __ANDROID_DEBUGGABLE__

    _hidl_status.setFromStatusT(_hidl_err);
    return ::android::hardware::Return<void>();

_hidl_error:
    _hidl_status.setFromStatusT(_hidl_err);
    return ::android::hardware::Return<void>(_hidl_status);
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::_hidl_getCacaoInterface_V2_0(::android::hardware::IInterface *_hidl_this, ::android::hardware::details::HidlInstrumentor *_hidl_this_instrumentor, getCacaoInterface_V2_0_cb _hidl_cb) {
    #ifdef __ANDROID_DEBUGGABLE__
    bool mEnableInstrumentation = _hidl_this_instrumentor->isInstrumentationEnabled();
    const auto &mInstrumentationCallbacks = _hidl_this_instrumentor->getInstrumentationCallbacks();
    #else
    (void) _hidl_this_instrumentor;
    #endif // __ANDROID_DEBUGGABLE__
    if (_hidl_cb == nullptr) {
        return ::android::hardware::Status::fromExceptionCode(
                ::android::hardware::Status::EX_ILLEGAL_ARGUMENT,
                "Null synchronous callback passed.");
    }

    atrace_begin(ATRACE_TAG_HAL, "HIDL::IVendorSomcCameraProvider::getCacaoInterface_V2_0::client");
    #ifdef __ANDROID_DEBUGGABLE__
    if (UNLIKELY(mEnableInstrumentation)) {
        std::vector<void *> _hidl_args;
        for (const auto &callback: mInstrumentationCallbacks) {
            callback(InstrumentationEvent::CLIENT_API_ENTRY, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCacaoInterface_V2_0", &_hidl_args);
        }
    }
    #endif // __ANDROID_DEBUGGABLE__

    ::android::hardware::Parcel _hidl_data;
    ::android::hardware::Parcel _hidl_reply;
    ::android::status_t _hidl_err;
    ::android::hardware::Status _hidl_status;

    ::android::hardware::camera::common::V1_0::Status _hidl_out_status;
    ::android::sp<::vendor::somc::hardware::camera::cacao::V2_0::ICacao> _hidl_out_service;

    _hidl_err = _hidl_data.writeInterfaceToken(BpHwVendorSomcCameraProvider::descriptor);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    _hidl_err = ::android::hardware::IInterface::asBinder(_hidl_this)->transact(9 /* getCacaoInterface_V2_0 */, _hidl_data, &_hidl_reply);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    _hidl_err = ::android::hardware::readFromParcel(&_hidl_status, _hidl_reply);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    if (!_hidl_status.isOk()) { return _hidl_status; }

    _hidl_err = _hidl_reply.readUint32((uint32_t *)&_hidl_out_status);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    {
        ::android::sp<::android::hardware::IBinder> _hidl_binder;
        _hidl_err = _hidl_reply.readNullableStrongBinder(&_hidl_binder);
        if (_hidl_err != ::android::OK) { goto _hidl_error; }

        _hidl_out_service = ::android::hardware::fromBinder<::vendor::somc::hardware::camera::cacao::V2_0::ICacao,::vendor::somc::hardware::camera::cacao::V2_0::BpHwCacao,::vendor::somc::hardware::camera::cacao::V2_0::BnHwCacao>(_hidl_binder);
    }

    _hidl_cb(_hidl_out_status, _hidl_out_service);

    atrace_end(ATRACE_TAG_HAL);
    #ifdef __ANDROID_DEBUGGABLE__
    if (UNLIKELY(mEnableInstrumentation)) {
        std::vector<void *> _hidl_args;
        _hidl_args.push_back((void *)&_hidl_out_status);
        _hidl_args.push_back((void *)&_hidl_out_service);
        for (const auto &callback: mInstrumentationCallbacks) {
            callback(InstrumentationEvent::CLIENT_API_EXIT, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCacaoInterface_V2_0", &_hidl_args);
        }
    }
    #endif // __ANDROID_DEBUGGABLE__

    _hidl_status.setFromStatusT(_hidl_err);
    return ::android::hardware::Return<void>();

_hidl_error:
    _hidl_status.setFromStatusT(_hidl_err);
    return ::android::hardware::Return<void>(_hidl_status);
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::_hidl_getCacaoInterface_V3_0(::android::hardware::IInterface *_hidl_this, ::android::hardware::details::HidlInstrumentor *_hidl_this_instrumentor, getCacaoInterface_V3_0_cb _hidl_cb) {
    #ifdef __ANDROID_DEBUGGABLE__
    bool mEnableInstrumentation = _hidl_this_instrumentor->isInstrumentationEnabled();
    const auto &mInstrumentationCallbacks = _hidl_this_instrumentor->getInstrumentationCallbacks();
    #else
    (void) _hidl_this_instrumentor;
    #endif // __ANDROID_DEBUGGABLE__
    if (_hidl_cb == nullptr) {
        return ::android::hardware::Status::fromExceptionCode(
                ::android::hardware::Status::EX_ILLEGAL_ARGUMENT,
                "Null synchronous callback passed.");
    }

    atrace_begin(ATRACE_TAG_HAL, "HIDL::IVendorSomcCameraProvider::getCacaoInterface_V3_0::client");
    #ifdef __ANDROID_DEBUGGABLE__
    if (UNLIKELY(mEnableInstrumentation)) {
        std::vector<void *> _hidl_args;
        for (const auto &callback: mInstrumentationCallbacks) {
            callback(InstrumentationEvent::CLIENT_API_ENTRY, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCacaoInterface_V3_0", &_hidl_args);
        }
    }
    #endif // __ANDROID_DEBUGGABLE__

    ::android::hardware::Parcel _hidl_data;
    ::android::hardware::Parcel _hidl_reply;
    ::android::status_t _hidl_err;
    ::android::hardware::Status _hidl_status;

    ::android::hardware::camera::common::V1_0::Status _hidl_out_status;
    ::android::sp<::vendor::somc::hardware::camera::cacao::V3_0::ICacao> _hidl_out_service;

    _hidl_err = _hidl_data.writeInterfaceToken(BpHwVendorSomcCameraProvider::descriptor);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    _hidl_err = ::android::hardware::IInterface::asBinder(_hidl_this)->transact(10 /* getCacaoInterface_V3_0 */, _hidl_data, &_hidl_reply);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    _hidl_err = ::android::hardware::readFromParcel(&_hidl_status, _hidl_reply);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    if (!_hidl_status.isOk()) { return _hidl_status; }

    _hidl_err = _hidl_reply.readUint32((uint32_t *)&_hidl_out_status);
    if (_hidl_err != ::android::OK) { goto _hidl_error; }

    {
        ::android::sp<::android::hardware::IBinder> _hidl_binder;
        _hidl_err = _hidl_reply.readNullableStrongBinder(&_hidl_binder);
        if (_hidl_err != ::android::OK) { goto _hidl_error; }

        _hidl_out_service = ::android::hardware::fromBinder<::vendor::somc::hardware::camera::cacao::V3_0::ICacao,::vendor::somc::hardware::camera::cacao::V3_0::BpHwCacao,::vendor::somc::hardware::camera::cacao::V3_0::BnHwCacao>(_hidl_binder);
    }

    _hidl_cb(_hidl_out_status, _hidl_out_service);

    atrace_end(ATRACE_TAG_HAL);
    #ifdef __ANDROID_DEBUGGABLE__
    if (UNLIKELY(mEnableInstrumentation)) {
        std::vector<void *> _hidl_args;
        _hidl_args.push_back((void *)&_hidl_out_status);
        _hidl_args.push_back((void *)&_hidl_out_service);
        for (const auto &callback: mInstrumentationCallbacks) {
            callback(InstrumentationEvent::CLIENT_API_EXIT, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCacaoInterface_V3_0", &_hidl_args);
        }
    }
    #endif // __ANDROID_DEBUGGABLE__

    _hidl_status.setFromStatusT(_hidl_err);
    return ::android::hardware::Return<void>();

_hidl_error:
    _hidl_status.setFromStatusT(_hidl_err);
    return ::android::hardware::Return<void>(_hidl_status);
}


// Methods from ::android::hardware::camera::provider::V2_4::ICameraProvider follow.
::android::hardware::Return<::android::hardware::camera::common::V1_0::Status> BpHwVendorSomcCameraProvider::setCallback(const ::android::sp<::android::hardware::camera::provider::V2_4::ICameraProviderCallback>& callback){
    ::android::hardware::Return<::android::hardware::camera::common::V1_0::Status>  _hidl_out = ::android::hardware::camera::provider::V2_4::BpHwCameraProvider::_hidl_setCallback(this, this, callback);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::getVendorTags(getVendorTags_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::android::hardware::camera::provider::V2_4::BpHwCameraProvider::_hidl_getVendorTags(this, this, _hidl_cb);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::getCameraIdList(getCameraIdList_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::android::hardware::camera::provider::V2_4::BpHwCameraProvider::_hidl_getCameraIdList(this, this, _hidl_cb);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::isSetTorchModeSupported(isSetTorchModeSupported_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::android::hardware::camera::provider::V2_4::BpHwCameraProvider::_hidl_isSetTorchModeSupported(this, this, _hidl_cb);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::getCameraDeviceInterface_V1_x(const ::android::hardware::hidl_string& cameraDeviceName, getCameraDeviceInterface_V1_x_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::android::hardware::camera::provider::V2_4::BpHwCameraProvider::_hidl_getCameraDeviceInterface_V1_x(this, this, cameraDeviceName, _hidl_cb);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::getCameraDeviceInterface_V3_x(const ::android::hardware::hidl_string& cameraDeviceName, getCameraDeviceInterface_V3_x_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::android::hardware::camera::provider::V2_4::BpHwCameraProvider::_hidl_getCameraDeviceInterface_V3_x(this, this, cameraDeviceName, _hidl_cb);

    return _hidl_out;
}


// Methods from ::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider follow.
::android::hardware::Return<void> BpHwVendorSomcCameraProvider::getCameraExtensionDeviceInterface_V1_0(const ::android::hardware::hidl_string& cameraDeviceName, getCameraExtensionDeviceInterface_V1_0_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::vendor::somc::hardware::camera::provider::V1_0::BpHwVendorSomcCameraProvider::_hidl_getCameraExtensionDeviceInterface_V1_0(this, this, cameraDeviceName, _hidl_cb);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::getCacaoInterface_V1_0(getCacaoInterface_V1_0_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::vendor::somc::hardware::camera::provider::V1_0::BpHwVendorSomcCameraProvider::_hidl_getCacaoInterface_V1_0(this, this, _hidl_cb);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::getCacaoInterface_V2_0(getCacaoInterface_V2_0_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::vendor::somc::hardware::camera::provider::V1_0::BpHwVendorSomcCameraProvider::_hidl_getCacaoInterface_V2_0(this, this, _hidl_cb);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::getCacaoInterface_V3_0(getCacaoInterface_V3_0_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::vendor::somc::hardware::camera::provider::V1_0::BpHwVendorSomcCameraProvider::_hidl_getCacaoInterface_V3_0(this, this, _hidl_cb);

    return _hidl_out;
}


// Methods from ::android::hidl::base::V1_0::IBase follow.
::android::hardware::Return<void> BpHwVendorSomcCameraProvider::interfaceChain(interfaceChain_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::android::hidl::base::V1_0::BpHwBase::_hidl_interfaceChain(this, this, _hidl_cb);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::debug(const ::android::hardware::hidl_handle& fd, const ::android::hardware::hidl_vec<::android::hardware::hidl_string>& options){
    ::android::hardware::Return<void>  _hidl_out = ::android::hidl::base::V1_0::BpHwBase::_hidl_debug(this, this, fd, options);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::interfaceDescriptor(interfaceDescriptor_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::android::hidl::base::V1_0::BpHwBase::_hidl_interfaceDescriptor(this, this, _hidl_cb);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::getHashChain(getHashChain_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::android::hidl::base::V1_0::BpHwBase::_hidl_getHashChain(this, this, _hidl_cb);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::setHALInstrumentation(){
    ::android::hardware::Return<void>  _hidl_out = ::android::hidl::base::V1_0::BpHwBase::_hidl_setHALInstrumentation(this, this);

    return _hidl_out;
}

::android::hardware::Return<bool> BpHwVendorSomcCameraProvider::linkToDeath(const ::android::sp<::android::hardware::hidl_death_recipient>& recipient, uint64_t cookie){
    ::android::hardware::ProcessState::self()->startThreadPool();
    ::android::hardware::hidl_binder_death_recipient *binder_recipient = new ::android::hardware::hidl_binder_death_recipient(recipient, cookie, this);
    std::unique_lock<std::mutex> lock(_hidl_mMutex);
    _hidl_mDeathRecipients.push_back(binder_recipient);
    return (remote()->linkToDeath(binder_recipient) == ::android::OK);
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::ping(){
    ::android::hardware::Return<void>  _hidl_out = ::android::hidl::base::V1_0::BpHwBase::_hidl_ping(this, this);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::getDebugInfo(getDebugInfo_cb _hidl_cb){
    ::android::hardware::Return<void>  _hidl_out = ::android::hidl::base::V1_0::BpHwBase::_hidl_getDebugInfo(this, this, _hidl_cb);

    return _hidl_out;
}

::android::hardware::Return<void> BpHwVendorSomcCameraProvider::notifySyspropsChanged(){
    ::android::hardware::Return<void>  _hidl_out = ::android::hidl::base::V1_0::BpHwBase::_hidl_notifySyspropsChanged(this, this);

    return _hidl_out;
}

::android::hardware::Return<bool> BpHwVendorSomcCameraProvider::unlinkToDeath(const ::android::sp<::android::hardware::hidl_death_recipient>& recipient){
    std::unique_lock<std::mutex> lock(_hidl_mMutex);
    for (auto it = _hidl_mDeathRecipients.begin();it != _hidl_mDeathRecipients.end();++it) {
        if ((*it)->getRecipient() == recipient) {
            ::android::status_t status = remote()->unlinkToDeath(*it);
            _hidl_mDeathRecipients.erase(it);
            return status == ::android::OK;
        }}
    return false;
}


BnHwVendorSomcCameraProvider::BnHwVendorSomcCameraProvider(const ::android::sp<IVendorSomcCameraProvider> &_hidl_impl)
        : ::android::hidl::base::V1_0::BnHwBase(_hidl_impl, "vendor.somc.hardware.camera.provider@1.0", "IVendorSomcCameraProvider") { 
            _hidl_mImpl = _hidl_impl;
            auto prio = ::android::hardware::details::gServicePrioMap.get(_hidl_impl, {SCHED_NORMAL, 0});
            mSchedPolicy = prio.sched_policy;
            mSchedPriority = prio.prio;
            setRequestingSid(::android::hardware::details::gServiceSidMap.get(_hidl_impl, false));
}

BnHwVendorSomcCameraProvider::~BnHwVendorSomcCameraProvider() {
    ::android::hardware::details::gBnMap.eraseIfEqual(_hidl_mImpl.get(), this);
}

// Methods from ::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider follow.
::android::status_t BnHwVendorSomcCameraProvider::_hidl_getCameraExtensionDeviceInterface_V1_0(
        ::android::hidl::base::V1_0::BnHwBase* _hidl_this,
        const ::android::hardware::Parcel &_hidl_data,
        ::android::hardware::Parcel *_hidl_reply,
        TransactCallback _hidl_cb) {
    #ifdef __ANDROID_DEBUGGABLE__
    bool mEnableInstrumentation = _hidl_this->isInstrumentationEnabled();
    const auto &mInstrumentationCallbacks = _hidl_this->getInstrumentationCallbacks();
    #endif // __ANDROID_DEBUGGABLE__

    ::android::status_t _hidl_err = ::android::OK;
    if (!_hidl_data.enforceInterface(BnHwVendorSomcCameraProvider::Pure::descriptor)) {
        _hidl_err = ::android::BAD_TYPE;
        return _hidl_err;
    }

    const ::android::hardware::hidl_string* cameraDeviceName;

    size_t _hidl_cameraDeviceName_parent;

    _hidl_err = _hidl_data.readBuffer(sizeof(*cameraDeviceName), &_hidl_cameraDeviceName_parent,  reinterpret_cast<const void **>(&cameraDeviceName));

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    _hidl_err = ::android::hardware::readEmbeddedFromParcel(
            const_cast<::android::hardware::hidl_string &>(*cameraDeviceName),
            _hidl_data,
            _hidl_cameraDeviceName_parent,
            0 /* parentOffset */);

    if (_hidl_err != ::android::OK) { return _hidl_err; }

    atrace_begin(ATRACE_TAG_HAL, "HIDL::IVendorSomcCameraProvider::getCameraExtensionDeviceInterface_V1_0::server");
    #ifdef __ANDROID_DEBUGGABLE__
    if (UNLIKELY(mEnableInstrumentation)) {
        std::vector<void *> _hidl_args;
        _hidl_args.push_back((void *)cameraDeviceName);
        for (const auto &callback: mInstrumentationCallbacks) {
            callback(InstrumentationEvent::SERVER_API_ENTRY, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCameraExtensionDeviceInterface_V1_0", &_hidl_args);
        }
    }
    #endif // __ANDROID_DEBUGGABLE__

    bool _hidl_callbackCalled = false;

    static_cast<IVendorSomcCameraProvider*>(_hidl_this->getImpl().get())->getCameraExtensionDeviceInterface_V1_0(*cameraDeviceName, [&](const auto &_hidl_out_status, const auto &_hidl_out_device) {
        if (_hidl_callbackCalled) {
            LOG_ALWAYS_FATAL("getCameraExtensionDeviceInterface_V1_0: _hidl_cb called a second time, but must be called once.");
        }
        _hidl_callbackCalled = true;

        ::android::hardware::writeToParcel(::android::hardware::Status::ok(), _hidl_reply);

        _hidl_err = _hidl_reply->writeUint32((uint32_t)_hidl_out_status);
        /* _hidl_err ignored! */

        if (_hidl_out_device == nullptr) {
            _hidl_err = _hidl_reply->writeStrongBinder(nullptr);
        } else {
            ::android::sp<::android::hardware::IBinder> _hidl_binder = ::android::hardware::toBinder<
                    ::vendor::somc::hardware::camera::device::V1_0::ICameraExtensionDevice>(_hidl_out_device);
            if (_hidl_binder.get() != nullptr) {
                _hidl_err = _hidl_reply->writeStrongBinder(_hidl_binder);
            } else {
                _hidl_err = ::android::UNKNOWN_ERROR;
            }
        }
        /* _hidl_err ignored! */

        atrace_end(ATRACE_TAG_HAL);
        #ifdef __ANDROID_DEBUGGABLE__
        if (UNLIKELY(mEnableInstrumentation)) {
            std::vector<void *> _hidl_args;
            _hidl_args.push_back((void *)&_hidl_out_status);
            _hidl_args.push_back((void *)&_hidl_out_device);
            for (const auto &callback: mInstrumentationCallbacks) {
                callback(InstrumentationEvent::SERVER_API_EXIT, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCameraExtensionDeviceInterface_V1_0", &_hidl_args);
            }
        }
        #endif // __ANDROID_DEBUGGABLE__

        _hidl_cb(*_hidl_reply);
    });

    if (!_hidl_callbackCalled) {
        LOG_ALWAYS_FATAL("getCameraExtensionDeviceInterface_V1_0: _hidl_cb not called, but must be called once.");
    }

    return _hidl_err;
}

::android::status_t BnHwVendorSomcCameraProvider::_hidl_getCacaoInterface_V1_0(
        ::android::hidl::base::V1_0::BnHwBase* _hidl_this,
        const ::android::hardware::Parcel &_hidl_data,
        ::android::hardware::Parcel *_hidl_reply,
        TransactCallback _hidl_cb) {
    #ifdef __ANDROID_DEBUGGABLE__
    bool mEnableInstrumentation = _hidl_this->isInstrumentationEnabled();
    const auto &mInstrumentationCallbacks = _hidl_this->getInstrumentationCallbacks();
    #endif // __ANDROID_DEBUGGABLE__

    ::android::status_t _hidl_err = ::android::OK;
    if (!_hidl_data.enforceInterface(BnHwVendorSomcCameraProvider::Pure::descriptor)) {
        _hidl_err = ::android::BAD_TYPE;
        return _hidl_err;
    }

    atrace_begin(ATRACE_TAG_HAL, "HIDL::IVendorSomcCameraProvider::getCacaoInterface_V1_0::server");
    #ifdef __ANDROID_DEBUGGABLE__
    if (UNLIKELY(mEnableInstrumentation)) {
        std::vector<void *> _hidl_args;
        for (const auto &callback: mInstrumentationCallbacks) {
            callback(InstrumentationEvent::SERVER_API_ENTRY, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCacaoInterface_V1_0", &_hidl_args);
        }
    }
    #endif // __ANDROID_DEBUGGABLE__

    bool _hidl_callbackCalled = false;

    static_cast<IVendorSomcCameraProvider*>(_hidl_this->getImpl().get())->getCacaoInterface_V1_0([&](const auto &_hidl_out_status, const auto &_hidl_out_service) {
        if (_hidl_callbackCalled) {
            LOG_ALWAYS_FATAL("getCacaoInterface_V1_0: _hidl_cb called a second time, but must be called once.");
        }
        _hidl_callbackCalled = true;

        ::android::hardware::writeToParcel(::android::hardware::Status::ok(), _hidl_reply);

        _hidl_err = _hidl_reply->writeUint32((uint32_t)_hidl_out_status);
        /* _hidl_err ignored! */

        if (_hidl_out_service == nullptr) {
            _hidl_err = _hidl_reply->writeStrongBinder(nullptr);
        } else {
            ::android::sp<::android::hardware::IBinder> _hidl_binder = ::android::hardware::toBinder<
                    ::vendor::somc::hardware::camera::cacao::V1_0::ICacao>(_hidl_out_service);
            if (_hidl_binder.get() != nullptr) {
                _hidl_err = _hidl_reply->writeStrongBinder(_hidl_binder);
            } else {
                _hidl_err = ::android::UNKNOWN_ERROR;
            }
        }
        /* _hidl_err ignored! */

        atrace_end(ATRACE_TAG_HAL);
        #ifdef __ANDROID_DEBUGGABLE__
        if (UNLIKELY(mEnableInstrumentation)) {
            std::vector<void *> _hidl_args;
            _hidl_args.push_back((void *)&_hidl_out_status);
            _hidl_args.push_back((void *)&_hidl_out_service);
            for (const auto &callback: mInstrumentationCallbacks) {
                callback(InstrumentationEvent::SERVER_API_EXIT, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCacaoInterface_V1_0", &_hidl_args);
            }
        }
        #endif // __ANDROID_DEBUGGABLE__

        _hidl_cb(*_hidl_reply);
    });

    if (!_hidl_callbackCalled) {
        LOG_ALWAYS_FATAL("getCacaoInterface_V1_0: _hidl_cb not called, but must be called once.");
    }

    return _hidl_err;
}

::android::status_t BnHwVendorSomcCameraProvider::_hidl_getCacaoInterface_V2_0(
        ::android::hidl::base::V1_0::BnHwBase* _hidl_this,
        const ::android::hardware::Parcel &_hidl_data,
        ::android::hardware::Parcel *_hidl_reply,
        TransactCallback _hidl_cb) {
    #ifdef __ANDROID_DEBUGGABLE__
    bool mEnableInstrumentation = _hidl_this->isInstrumentationEnabled();
    const auto &mInstrumentationCallbacks = _hidl_this->getInstrumentationCallbacks();
    #endif // __ANDROID_DEBUGGABLE__

    ::android::status_t _hidl_err = ::android::OK;
    if (!_hidl_data.enforceInterface(BnHwVendorSomcCameraProvider::Pure::descriptor)) {
        _hidl_err = ::android::BAD_TYPE;
        return _hidl_err;
    }

    atrace_begin(ATRACE_TAG_HAL, "HIDL::IVendorSomcCameraProvider::getCacaoInterface_V2_0::server");
    #ifdef __ANDROID_DEBUGGABLE__
    if (UNLIKELY(mEnableInstrumentation)) {
        std::vector<void *> _hidl_args;
        for (const auto &callback: mInstrumentationCallbacks) {
            callback(InstrumentationEvent::SERVER_API_ENTRY, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCacaoInterface_V2_0", &_hidl_args);
        }
    }
    #endif // __ANDROID_DEBUGGABLE__

    bool _hidl_callbackCalled = false;

    static_cast<IVendorSomcCameraProvider*>(_hidl_this->getImpl().get())->getCacaoInterface_V2_0([&](const auto &_hidl_out_status, const auto &_hidl_out_service) {
        if (_hidl_callbackCalled) {
            LOG_ALWAYS_FATAL("getCacaoInterface_V2_0: _hidl_cb called a second time, but must be called once.");
        }
        _hidl_callbackCalled = true;

        ::android::hardware::writeToParcel(::android::hardware::Status::ok(), _hidl_reply);

        _hidl_err = _hidl_reply->writeUint32((uint32_t)_hidl_out_status);
        /* _hidl_err ignored! */

        if (_hidl_out_service == nullptr) {
            _hidl_err = _hidl_reply->writeStrongBinder(nullptr);
        } else {
            ::android::sp<::android::hardware::IBinder> _hidl_binder = ::android::hardware::toBinder<
                    ::vendor::somc::hardware::camera::cacao::V2_0::ICacao>(_hidl_out_service);
            if (_hidl_binder.get() != nullptr) {
                _hidl_err = _hidl_reply->writeStrongBinder(_hidl_binder);
            } else {
                _hidl_err = ::android::UNKNOWN_ERROR;
            }
        }
        /* _hidl_err ignored! */

        atrace_end(ATRACE_TAG_HAL);
        #ifdef __ANDROID_DEBUGGABLE__
        if (UNLIKELY(mEnableInstrumentation)) {
            std::vector<void *> _hidl_args;
            _hidl_args.push_back((void *)&_hidl_out_status);
            _hidl_args.push_back((void *)&_hidl_out_service);
            for (const auto &callback: mInstrumentationCallbacks) {
                callback(InstrumentationEvent::SERVER_API_EXIT, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCacaoInterface_V2_0", &_hidl_args);
            }
        }
        #endif // __ANDROID_DEBUGGABLE__

        _hidl_cb(*_hidl_reply);
    });

    if (!_hidl_callbackCalled) {
        LOG_ALWAYS_FATAL("getCacaoInterface_V2_0: _hidl_cb not called, but must be called once.");
    }

    return _hidl_err;
}

::android::status_t BnHwVendorSomcCameraProvider::_hidl_getCacaoInterface_V3_0(
        ::android::hidl::base::V1_0::BnHwBase* _hidl_this,
        const ::android::hardware::Parcel &_hidl_data,
        ::android::hardware::Parcel *_hidl_reply,
        TransactCallback _hidl_cb) {
    #ifdef __ANDROID_DEBUGGABLE__
    bool mEnableInstrumentation = _hidl_this->isInstrumentationEnabled();
    const auto &mInstrumentationCallbacks = _hidl_this->getInstrumentationCallbacks();
    #endif // __ANDROID_DEBUGGABLE__

    ::android::status_t _hidl_err = ::android::OK;
    if (!_hidl_data.enforceInterface(BnHwVendorSomcCameraProvider::Pure::descriptor)) {
        _hidl_err = ::android::BAD_TYPE;
        return _hidl_err;
    }

    atrace_begin(ATRACE_TAG_HAL, "HIDL::IVendorSomcCameraProvider::getCacaoInterface_V3_0::server");
    #ifdef __ANDROID_DEBUGGABLE__
    if (UNLIKELY(mEnableInstrumentation)) {
        std::vector<void *> _hidl_args;
        for (const auto &callback: mInstrumentationCallbacks) {
            callback(InstrumentationEvent::SERVER_API_ENTRY, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCacaoInterface_V3_0", &_hidl_args);
        }
    }
    #endif // __ANDROID_DEBUGGABLE__

    bool _hidl_callbackCalled = false;

    static_cast<IVendorSomcCameraProvider*>(_hidl_this->getImpl().get())->getCacaoInterface_V3_0([&](const auto &_hidl_out_status, const auto &_hidl_out_service) {
        if (_hidl_callbackCalled) {
            LOG_ALWAYS_FATAL("getCacaoInterface_V3_0: _hidl_cb called a second time, but must be called once.");
        }
        _hidl_callbackCalled = true;

        ::android::hardware::writeToParcel(::android::hardware::Status::ok(), _hidl_reply);

        _hidl_err = _hidl_reply->writeUint32((uint32_t)_hidl_out_status);
        /* _hidl_err ignored! */

        if (_hidl_out_service == nullptr) {
            _hidl_err = _hidl_reply->writeStrongBinder(nullptr);
        } else {
            ::android::sp<::android::hardware::IBinder> _hidl_binder = ::android::hardware::toBinder<
                    ::vendor::somc::hardware::camera::cacao::V3_0::ICacao>(_hidl_out_service);
            if (_hidl_binder.get() != nullptr) {
                _hidl_err = _hidl_reply->writeStrongBinder(_hidl_binder);
            } else {
                _hidl_err = ::android::UNKNOWN_ERROR;
            }
        }
        /* _hidl_err ignored! */

        atrace_end(ATRACE_TAG_HAL);
        #ifdef __ANDROID_DEBUGGABLE__
        if (UNLIKELY(mEnableInstrumentation)) {
            std::vector<void *> _hidl_args;
            _hidl_args.push_back((void *)&_hidl_out_status);
            _hidl_args.push_back((void *)&_hidl_out_service);
            for (const auto &callback: mInstrumentationCallbacks) {
                callback(InstrumentationEvent::SERVER_API_EXIT, "vendor.somc.hardware.camera.provider", "1.0", "IVendorSomcCameraProvider", "getCacaoInterface_V3_0", &_hidl_args);
            }
        }
        #endif // __ANDROID_DEBUGGABLE__

        _hidl_cb(*_hidl_reply);
    });

    if (!_hidl_callbackCalled) {
        LOG_ALWAYS_FATAL("getCacaoInterface_V3_0: _hidl_cb not called, but must be called once.");
    }

    return _hidl_err;
}


// Methods from ::android::hardware::camera::provider::V2_4::ICameraProvider follow.

// Methods from ::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider follow.

// Methods from ::android::hidl::base::V1_0::IBase follow.
::android::hardware::Return<void> BnHwVendorSomcCameraProvider::ping() {
    return ::android::hardware::Void();
}
::android::hardware::Return<void> BnHwVendorSomcCameraProvider::getDebugInfo(getDebugInfo_cb _hidl_cb) {
    ::android::hidl::base::V1_0::DebugInfo info = {};
    info.pid = ::android::hardware::details::getPidIfSharable();
    info.ptr = ::android::hardware::details::debuggable()? reinterpret_cast<uint64_t>(this) : 0;
    info.arch = 
    #if defined(__LP64__)
    ::android::hidl::base::V1_0::DebugInfo::Architecture::IS_64BIT
    #else
    ::android::hidl::base::V1_0::DebugInfo::Architecture::IS_32BIT
    #endif
    ;
    _hidl_cb(info);
    return ::android::hardware::Void();
}

::android::status_t BnHwVendorSomcCameraProvider::onTransact(
        uint32_t _hidl_code,
        const ::android::hardware::Parcel &_hidl_data,
        ::android::hardware::Parcel *_hidl_reply,
        uint32_t _hidl_flags,
        TransactCallback _hidl_cb) {
    ::android::status_t _hidl_err = ::android::OK;

    switch (_hidl_code) {
        case 1 /* setCallback */:
        {
            bool _hidl_is_oneway = _hidl_flags & 1 /* oneway */;
            if (_hidl_is_oneway != false) {
                return ::android::UNKNOWN_ERROR;
            }

            _hidl_err = ::android::hardware::camera::provider::V2_4::BnHwCameraProvider::_hidl_setCallback(this, _hidl_data, _hidl_reply, _hidl_cb);
            break;
        }

        case 2 /* getVendorTags */:
        {
            bool _hidl_is_oneway = _hidl_flags & 1 /* oneway */;
            if (_hidl_is_oneway != false) {
                return ::android::UNKNOWN_ERROR;
            }

            _hidl_err = ::android::hardware::camera::provider::V2_4::BnHwCameraProvider::_hidl_getVendorTags(this, _hidl_data, _hidl_reply, _hidl_cb);
            break;
        }

        case 3 /* getCameraIdList */:
        {
            bool _hidl_is_oneway = _hidl_flags & 1 /* oneway */;
            if (_hidl_is_oneway != false) {
                return ::android::UNKNOWN_ERROR;
            }

            _hidl_err = ::android::hardware::camera::provider::V2_4::BnHwCameraProvider::_hidl_getCameraIdList(this, _hidl_data, _hidl_reply, _hidl_cb);
            break;
        }

        case 4 /* isSetTorchModeSupported */:
        {
            bool _hidl_is_oneway = _hidl_flags & 1 /* oneway */;
            if (_hidl_is_oneway != false) {
                return ::android::UNKNOWN_ERROR;
            }

            _hidl_err = ::android::hardware::camera::provider::V2_4::BnHwCameraProvider::_hidl_isSetTorchModeSupported(this, _hidl_data, _hidl_reply, _hidl_cb);
            break;
        }

        case 5 /* getCameraDeviceInterface_V1_x */:
        {
            bool _hidl_is_oneway = _hidl_flags & 1 /* oneway */;
            if (_hidl_is_oneway != false) {
                return ::android::UNKNOWN_ERROR;
            }

            _hidl_err = ::android::hardware::camera::provider::V2_4::BnHwCameraProvider::_hidl_getCameraDeviceInterface_V1_x(this, _hidl_data, _hidl_reply, _hidl_cb);
            break;
        }

        case 6 /* getCameraDeviceInterface_V3_x */:
        {
            bool _hidl_is_oneway = _hidl_flags & 1 /* oneway */;
            if (_hidl_is_oneway != false) {
                return ::android::UNKNOWN_ERROR;
            }

            _hidl_err = ::android::hardware::camera::provider::V2_4::BnHwCameraProvider::_hidl_getCameraDeviceInterface_V3_x(this, _hidl_data, _hidl_reply, _hidl_cb);
            break;
        }

        case 7 /* getCameraExtensionDeviceInterface_V1_0 */:
        {
            bool _hidl_is_oneway = _hidl_flags & 1 /* oneway */;
            if (_hidl_is_oneway != false) {
                return ::android::UNKNOWN_ERROR;
            }

            _hidl_err = ::vendor::somc::hardware::camera::provider::V1_0::BnHwVendorSomcCameraProvider::_hidl_getCameraExtensionDeviceInterface_V1_0(this, _hidl_data, _hidl_reply, _hidl_cb);
            break;
        }

        case 8 /* getCacaoInterface_V1_0 */:
        {
            bool _hidl_is_oneway = _hidl_flags & 1 /* oneway */;
            if (_hidl_is_oneway != false) {
                return ::android::UNKNOWN_ERROR;
            }

            _hidl_err = ::vendor::somc::hardware::camera::provider::V1_0::BnHwVendorSomcCameraProvider::_hidl_getCacaoInterface_V1_0(this, _hidl_data, _hidl_reply, _hidl_cb);
            break;
        }

        case 9 /* getCacaoInterface_V2_0 */:
        {
            bool _hidl_is_oneway = _hidl_flags & 1 /* oneway */;
            if (_hidl_is_oneway != false) {
                return ::android::UNKNOWN_ERROR;
            }

            _hidl_err = ::vendor::somc::hardware::camera::provider::V1_0::BnHwVendorSomcCameraProvider::_hidl_getCacaoInterface_V2_0(this, _hidl_data, _hidl_reply, _hidl_cb);
            break;
        }

        case 10 /* getCacaoInterface_V3_0 */:
        {
            bool _hidl_is_oneway = _hidl_flags & 1 /* oneway */;
            if (_hidl_is_oneway != false) {
                return ::android::UNKNOWN_ERROR;
            }

            _hidl_err = ::vendor::somc::hardware::camera::provider::V1_0::BnHwVendorSomcCameraProvider::_hidl_getCacaoInterface_V3_0(this, _hidl_data, _hidl_reply, _hidl_cb);
            break;
        }

        default:
        {
            return ::android::hidl::base::V1_0::BnHwBase::onTransact(
                    _hidl_code, _hidl_data, _hidl_reply, _hidl_flags, _hidl_cb);
        }
    }

    if (_hidl_err == ::android::UNEXPECTED_NULL) {
        _hidl_err = ::android::hardware::writeToParcel(
                ::android::hardware::Status::fromExceptionCode(::android::hardware::Status::EX_NULL_POINTER),
                _hidl_reply);
    }return _hidl_err;
}

BsVendorSomcCameraProvider::BsVendorSomcCameraProvider(const ::android::sp<::vendor::somc::hardware::camera::provider::V1_0::IVendorSomcCameraProvider> impl) : ::android::hardware::details::HidlInstrumentor("vendor.somc.hardware.camera.provider@1.0", "IVendorSomcCameraProvider"), mImpl(impl) {
    mOnewayQueue.start(3000 /* similar limit to binderized */);
}

::android::hardware::Return<void> BsVendorSomcCameraProvider::addOnewayTask(std::function<void(void)> fun) {
    if (!mOnewayQueue.push(fun)) {
        return ::android::hardware::Status::fromExceptionCode(
                ::android::hardware::Status::EX_TRANSACTION_FAILED,
                "Passthrough oneway function queue exceeds maximum size.");
    }
    return ::android::hardware::Status();
}

// static
::android::sp<IVendorSomcCameraProvider> IVendorSomcCameraProvider::tryGetService(const std::string &serviceName, const bool getStub) {
    return ::android::hardware::details::getServiceInternal<BpHwVendorSomcCameraProvider>(serviceName, false, getStub);
}

// static
::android::sp<IVendorSomcCameraProvider> IVendorSomcCameraProvider::getService(const std::string &serviceName, const bool getStub) {
    return ::android::hardware::details::getServiceInternal<BpHwVendorSomcCameraProvider>(serviceName, true, getStub);
}

::android::status_t IVendorSomcCameraProvider::registerAsService(const std::string &serviceName) {
    ::android::hardware::details::onRegistration("vendor.somc.hardware.camera.provider@1.0", "IVendorSomcCameraProvider", serviceName);

    const ::android::sp<::android::hidl::manager::V1_0::IServiceManager> sm
            = ::android::hardware::defaultServiceManager();
    if (sm == nullptr) {
        return ::android::INVALID_OPERATION;
    }
    ::android::hardware::Return<bool> ret = sm->add(serviceName.c_str(), this);
    return ret.isOk() && ret ? ::android::OK : ::android::UNKNOWN_ERROR;
}

bool IVendorSomcCameraProvider::registerForNotifications(
        const std::string &serviceName,
        const ::android::sp<::android::hidl::manager::V1_0::IServiceNotification> &notification) {
    const ::android::sp<::android::hidl::manager::V1_0::IServiceManager> sm
            = ::android::hardware::defaultServiceManager();
    if (sm == nullptr) {
        return false;
    }
    ::android::hardware::Return<bool> success =
            sm->registerForNotifications("vendor.somc.hardware.camera.provider@1.0::IVendorSomcCameraProvider",
                    serviceName, notification);
    return success.isOk() && success;
}

static_assert(sizeof(::android::hardware::MQDescriptor<char, ::android::hardware::kSynchronizedReadWrite>) == 32, "wrong size");
static_assert(sizeof(::android::hardware::hidl_handle) == 16, "wrong size");
static_assert(sizeof(::android::hardware::hidl_memory) == 40, "wrong size");
static_assert(sizeof(::android::hardware::hidl_string) == 16, "wrong size");
static_assert(sizeof(::android::hardware::hidl_vec<char>) == 16, "wrong size");

}  // namespace V1_0
}  // namespace provider
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor
