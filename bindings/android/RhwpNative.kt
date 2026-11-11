package rhwp.android

/**
 * JNI surface of `librhwp_android.so` (built by `scripts/package-android.sh`).
 * Every call returns the C ABI's JSON response as UTF-8 bytes.
 * Handles belong to the thread that created them: run all calls for one
 * document on a single dedicated thread (e.g. a single-thread executor).
 */
object RhwpNative {
  init {
    System.loadLibrary("rhwp_android")
  }

  /** Empty [data] opens a blank document. */
  @JvmStatic external fun open(data: ByteArray): ByteArray

  /** Opens a blank document and imports UTF-8 [html] into it. */
  @JvmStatic external fun openHtml(html: ByteArray): ByteArray

  @JvmStatic external fun request(handle: Long, request: ByteArray): ByteArray

  @JvmStatic external fun close(handle: Long): ByteArray

  /** Fills [destination], sized from the `byteLength` of the response that returned [buffer]. */
  @JvmStatic external fun bufferCopy(buffer: Long, destination: ByteArray): ByteArray

  @JvmStatic external fun bufferRelease(buffer: Long): ByteArray
}
