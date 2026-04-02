package com.vickhardth.attendance

import android.graphics.Bitmap
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Field
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import java.io.ByteArrayOutputStream
import java.io.File

data class Employee(
    val Name: String,
    val Mobile: String,
    val EmployeeID: String,
    val Role: String,
    val CompanyName: String,
    val LogoPath: String,
)

data class AttendanceRecord(
    val Name: String,
    val Date: String,
    val CheckIn: String,
    val CheckOut: String,
    val CheckInLocation: String,
    val CheckOutLocation: String,
    val WorkHours: String,
    val SourceFile: String,
)

data class HealthResponse(
    val status: String,
    val employees: Int,
    val attendance_rows: Int,
)

data class EmployeeCreateResponse(
    val message: String,
    val employee_count: Int,
    val sample_count: Int,
)

data class TrainResponse(
    val message: String,
    val model_file: String,
    val labels_file: String,
)

data class MarkResponse(
    val status: String,
    val name: String?,
    val confidence: Float?,
    val message: String,
)

interface AttendanceApi {
    @GET("health")
    suspend fun health(): HealthResponse

    @GET("employees")
    suspend fun employees(): List<Employee>

    @GET("attendance")
    suspend fun attendance(): List<AttendanceRecord>

    @Multipart
    @POST("employees/register")
    suspend fun registerEmployee(
        @Part("name") name: RequestBody,
        @Part("mobile") mobile: RequestBody,
        @Part("employee_id") employeeId: RequestBody,
        @Part("role") role: RequestBody,
        @Part("company_name") companyName: RequestBody,
        @Part("logo_path") logoPath: RequestBody,
        @Part sample: MultipartBody.Part?,
    ): EmployeeCreateResponse

    @POST("train")
    suspend fun train(): TrainResponse

    @Multipart
    @POST("attendance/mark")
    suspend fun markAttendance(
        @Part file: MultipartBody.Part,
    ): MarkResponse
}

object ApiFactory {
    fun create(baseUrl: String): AttendanceApi {
        val retrofit = Retrofit.Builder()
            .baseUrl(if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        return retrofit.create(AttendanceApi::class.java)
    }
}

fun textPart(value: String): RequestBody = value.toRequestBody("text/plain".toMediaType())

fun bitmapPart(bitmap: Bitmap, partName: String, fileName: String): MultipartBody.Part {
    val stream = ByteArrayOutputStream()
    bitmap.compress(Bitmap.CompressFormat.JPEG, 90, stream)
    val bytes = stream.toByteArray()
    val body = bytes.toRequestBody("image/jpeg".toMediaType())
    return MultipartBody.Part.createFormData(partName, fileName, body)
}

fun filePart(file: File, partName: String): MultipartBody.Part {
    val body = file.asRequestBody("image/jpeg".toMediaType())
    return MultipartBody.Part.createFormData(partName, file.name, body)
}
