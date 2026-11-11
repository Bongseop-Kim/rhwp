/* JNI bridge for bindings/Native (see ../swift/Sources/CRhwpNative/rhwp_native_ffi.h).
 * JSON travels as UTF-8 byte arrays: NewStringUTF takes modified UTF-8 and would
 * mangle supplementary characters. Handles belong to the calling OS thread, so
 * Kotlin must call every function of one document from the same thread. */
#include <jni.h>
#include <string.h>

#include "rhwp_native_ffi.h"

#define RHWP_JNI(name) JNIEXPORT jbyteArray JNICALL Java_rhwp_android_RhwpNative_##name

static jbyteArray take(JNIEnv *env, char *json) {
  if (!json) return NULL;
  jsize length = (jsize)strlen(json);
  jbyteArray out = (*env)->NewByteArray(env, length);
  if (out) (*env)->SetByteArrayRegion(env, out, 0, length, (const jbyte *)json);
  rhwp_string_free(json);
  return out;
}

RHWP_JNI(open)(JNIEnv *env, jclass type, jbyteArray data) {
  jsize length = (*env)->GetArrayLength(env, data);
  jbyte *bytes = (*env)->GetByteArrayElements(env, data, NULL);
  if (!bytes) return NULL;
  char *json = rhwp_session_open((const uint8_t *)bytes, (size_t)length, NULL, 0);
  (*env)->ReleaseByteArrayElements(env, data, bytes, JNI_ABORT);
  return take(env, json);
}

RHWP_JNI(openHtml)(JNIEnv *env, jclass type, jbyteArray html) {
  jsize length = (*env)->GetArrayLength(env, html);
  jbyte *bytes = (*env)->GetByteArrayElements(env, html, NULL);
  if (!bytes) return NULL;
  char *json = rhwp_session_open_html((const uint8_t *)bytes, (size_t)length);
  (*env)->ReleaseByteArrayElements(env, html, bytes, JNI_ABORT);
  return take(env, json);
}

RHWP_JNI(request)(JNIEnv *env, jclass type, jlong handle, jbyteArray request) {
  jsize length = (*env)->GetArrayLength(env, request);
  jbyte *bytes = (*env)->GetByteArrayElements(env, request, NULL);
  if (!bytes) return NULL;
  char *json = rhwp_session_request((uint64_t)handle, (const uint8_t *)bytes, (size_t)length);
  (*env)->ReleaseByteArrayElements(env, request, bytes, JNI_ABORT);
  return take(env, json);
}

RHWP_JNI(close)(JNIEnv *env, jclass type, jlong handle) {
  return take(env, rhwp_session_close((uint64_t)handle));
}

/* Fills destination (sized from the response's byteLength). Does not release the buffer. */
RHWP_JNI(bufferCopy)(JNIEnv *env, jclass type, jlong buffer, jbyteArray destination) {
  jsize capacity = (*env)->GetArrayLength(env, destination);
  jbyte *bytes = (*env)->GetByteArrayElements(env, destination, NULL);
  if (!bytes) return NULL;
  char *json = rhwp_session_buffer_copy((uint64_t)buffer, (uint8_t *)bytes, (size_t)capacity);
  (*env)->ReleaseByteArrayElements(env, destination, bytes, 0);
  return take(env, json);
}

RHWP_JNI(bufferRelease)(JNIEnv *env, jclass type, jlong buffer) {
  return take(env, rhwp_session_buffer_release((uint64_t)buffer));
}
