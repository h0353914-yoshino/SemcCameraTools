// C++ 用的 <stdatomic.h> 替代品（只給 libcacao 的 HIDL 介面庫與 libcammw_util 用）。
//
// liblog 的 log/log.h → cutils/trace.h 會 #include <stdatomic.h>。NDK 21 的 clang
// 版 stdatomic.h 會定義 atomic_is_lock_free / memory_order_* 等巨集，之後 libc++
// 的 <atomic>、<memory> 就會被打壞。這裡只提供 C++ 型別與 A9 cutils/trace.h 會用到的
// 名稱，不用巨集覆蓋 libc++ 的識別字。
#pragma once

#include <atomic>

using atomic_bool = std::atomic<bool>;

static constexpr std::memory_order memory_order_relaxed = std::memory_order_relaxed;
static constexpr std::memory_order memory_order_acquire = std::memory_order_acquire;
static constexpr std::memory_order memory_order_release = std::memory_order_release;
static constexpr std::memory_order memory_order_seq_cst = std::memory_order_seq_cst;

// 非模板多載，比 std 的 volatile 版本更精確，避免 ADL 造成的歧義
inline bool atomic_load_explicit(const std::atomic<bool>* obj, std::memory_order order) {
    return obj->load(order);
}
