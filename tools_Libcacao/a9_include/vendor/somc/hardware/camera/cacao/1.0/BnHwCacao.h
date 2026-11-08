#ifndef HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V1_0_BNHWCACAO_H
#define HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V1_0_BNHWCACAO_H

#include <vendor/somc/hardware/camera/cacao/1.0/IHwCacao.h>

namespace vendor {
namespace somc {
namespace hardware {
namespace camera {
namespace cacao {
namespace V1_0 {

struct BnHwCacao : public ::android::hidl::base::V1_0::BnHwBase {
    explicit BnHwCacao(const ::android::sp<ICacao> &_hidl_impl);
    explicit BnHwCacao(const ::android::sp<ICacao> &_hidl_impl, const std::string& HidlInstrumentor_package, const std::string& HidlInstrumentor_interface);

    virtual ~BnHwCacao();

    ::android::status_t onTransact(
            uint32_t _hidl_code,
            const ::android::hardware::Parcel &_hidl_data,
            ::android::hardware::Parcel *_hidl_reply,
            uint32_t _hidl_flags = 0,
            TransactCallback _hidl_cb = nullptr) override;


    typedef ICacao Pure;

    typedef android::hardware::details::bnhw_tag _hidl_tag;

    ::android::sp<ICacao> getImpl() { return _hidl_mImpl; }

private:
    // Methods from ::android::hidl::base::V1_0::IBase follow.
    ::android::hardware::Return<void> ping();
    using getDebugInfo_cb = ::android::hidl::base::V1_0::IBase::getDebugInfo_cb;
    ::android::hardware::Return<void> getDebugInfo(getDebugInfo_cb _hidl_cb);

    ::android::sp<ICacao> _hidl_mImpl;
};

}  // namespace V1_0
}  // namespace cacao
}  // namespace camera
}  // namespace hardware
}  // namespace somc
}  // namespace vendor

#endif  // HIDL_GENERATED_VENDOR_SOMC_HARDWARE_CAMERA_CACAO_V1_0_BNHWCACAO_H
