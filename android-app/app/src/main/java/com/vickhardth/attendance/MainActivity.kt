package com.vickhardth.attendance

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Divider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

private enum class CaptureTarget {
    None,
    Sample,
    Attendance,
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    AttendanceApp()
                }
            }
        }
    }
}

@Composable
private fun AttendanceApp() {
    val scope = rememberCoroutineScope()
    val context = androidx.compose.ui.platform.LocalContext.current

    var baseUrl by remember { mutableStateOf("http://10.0.2.2:8000") }
    var api by remember { mutableStateOf(ApiFactory.create(baseUrl)) }
    var health by remember { mutableStateOf<HealthResponse?>(null) }
    var employees by remember { mutableStateOf(listOf<Employee>()) }
    var attendance by remember { mutableStateOf(listOf<AttendanceRecord>()) }
    var status by remember { mutableStateOf("Ready") }

    var name by remember { mutableStateOf("") }
    var mobile by remember { mutableStateOf("") }
    var employeeId by remember { mutableStateOf("") }
    var role by remember { mutableStateOf("Employee") }
    var companyName by remember { mutableStateOf("Vickhardth Automation") }
    var logoPath by remember { mutableStateOf("") }
    var sampleBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var attendanceBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var captureTarget by remember { mutableStateOf(CaptureTarget.None) }
    var pendingCaptureUri by remember { mutableStateOf<Uri?>(null) }

    fun createCaptureUri(fileName: String): Uri {
        val imageDir = File(context.cacheDir, "images").apply { mkdirs() }
        val imageFile = File(imageDir, fileName)
        return FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            imageFile,
        )
    }

    val captureLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicture(),
    ) { success ->
        val uri = pendingCaptureUri
        if (!success || uri == null) {
            status = "Camera capture cancelled."
            captureTarget = CaptureTarget.None
            return@rememberLauncherForActivityResult
        }

        val bitmap = context.contentResolver.openInputStream(uri)?.use { stream ->
            BitmapFactory.decodeStream(stream)
        }

        when (captureTarget) {
            CaptureTarget.Sample -> sampleBitmap = bitmap
            CaptureTarget.Attendance -> attendanceBitmap = bitmap
            CaptureTarget.None -> Unit
        }

        captureTarget = CaptureTarget.None
        pendingCaptureUri = null
    }

    suspend fun refresh() {
        status = "Loading data..."
        try {
            val healthResponse = withContext(Dispatchers.IO) { api.health() }
            val employeeList = withContext(Dispatchers.IO) { api.employees() }
            val attendanceList = withContext(Dispatchers.IO) { api.attendance() }
            health = healthResponse
            employees = employeeList
            attendance = attendanceList
            status = "Connected to $baseUrl"
        } catch (exc: Exception) {
            status = "Load failed: ${exc.message ?: exc.javaClass.simpleName}"
        }
    }

    fun launchCamera(target: CaptureTarget) {
        captureTarget = target
        val fileName = if (target == CaptureTarget.Sample) {
            "sample_${System.currentTimeMillis()}.jpg"
        } else {
            "attendance_${System.currentTimeMillis()}.jpg"
        }
        pendingCaptureUri = createCaptureUri(fileName)
        captureLauncher.launch(pendingCaptureUri)
    }

    LaunchedEffect(baseUrl) {
        api = ApiFactory.create(baseUrl)
        refresh()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionCard(title = "Backend") {
            OutlinedTextField(
                value = baseUrl,
                onValueChange = { baseUrl = it.trim() },
                label = { Text("API Base URL") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(onClick = { scope.launch { refresh() } }) {
                    Text("Refresh")
                }
                Button(onClick = {
                    scope.launch {
                        status = "Training model..."
                        try {
                            val response = withContext(Dispatchers.IO) { api.train() }
                            status = response.message
                            refresh()
                        } catch (exc: Exception) {
                            status = "Train failed: ${exc.message ?: exc.javaClass.simpleName}"
                        }
                    }
                }) {
                    Text("Train")
                }
            }
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = status, fontWeight = FontWeight.SemiBold)
            health?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text("Employees: ${it.employees}")
                Text("Attendance rows: ${it.attendance_rows}")
            }
        }

        SectionCard(title = "Register Employee") {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Name") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = mobile, onValueChange = { mobile = it }, label = { Text("Mobile") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = employeeId, onValueChange = { employeeId = it }, label = { Text("Employee ID") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = role, onValueChange = { role = it }, label = { Text("Role") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = companyName, onValueChange = { companyName = it }, label = { Text("Company") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = logoPath, onValueChange = { logoPath = it }, label = { Text("Logo path optional") }, modifier = Modifier.fillMaxWidth())
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Button(onClick = { launchCamera(CaptureTarget.Sample) }) {
                        Text("Capture Sample")
                    }
                    if (sampleBitmap != null) {
                        Text("Sample ready")
                    }
                }
                sampleBitmap?.let { bitmap ->
                    Image(
                        bitmap = bitmap.asImageBitmap(),
                        contentDescription = "Sample preview",
                        modifier = Modifier.size(112.dp),
                    )
                }
                Button(onClick = {
                    scope.launch {
                        status = "Registering employee..."
                        try {
                            val samplePart = sampleBitmap?.let { bitmapPart(it, "samples", "sample.jpg") }
                            val response = withContext(Dispatchers.IO) {
                                api.registerEmployee(
                                    textPart(name),
                                    textPart(mobile),
                                    textPart(employeeId),
                                    textPart(role),
                                    textPart(companyName),
                                    textPart(logoPath),
                                    samplePart,
                                )
                            }
                            status = response.message
                            refresh()
                        } catch (exc: Exception) {
                            status = "Register failed: ${exc.message ?: exc.javaClass.simpleName}"
                        }
                    }
                }) {
                    Text("Register")
                }
            }
        }

        SectionCard(title = "Mark Attendance") {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Button(onClick = { launchCamera(CaptureTarget.Attendance) }) {
                        Text("Capture Face")
                    }
                    if (attendanceBitmap != null) {
                        Text("Photo ready")
                    }
                }
                attendanceBitmap?.let { bitmap ->
                    Image(
                        bitmap = bitmap.asImageBitmap(),
                        contentDescription = "Attendance preview",
                        modifier = Modifier.size(112.dp),
                    )
                }
                Button(onClick = {
                    val bitmap = attendanceBitmap
                    if (bitmap == null) {
                        status = "Capture a face photo first."
                        return@Button
                    }
                    scope.launch {
                        status = "Marking attendance..."
                        try {
                            val response = withContext(Dispatchers.IO) {
                                api.markAttendance(bitmapPart(bitmap, "file", "attendance.jpg"))
                            }
                            status = response.message
                            refresh()
                        } catch (exc: Exception) {
                            status = "Mark failed: ${exc.message ?: exc.javaClass.simpleName}"
                        }
                    }
                }) {
                    Text("Mark Attendance")
                }
            }
        }

        SectionCard(title = "Employees (${employees.size})") {
            employees.forEach { employee ->
                Column(modifier = Modifier.padding(vertical = 6.dp)) {
                    Text(employee.Name, fontWeight = FontWeight.SemiBold)
                    Text("${employee.EmployeeID} | ${employee.Role} | ${employee.Mobile}")
                }
                Divider()
            }
        }

        SectionCard(title = "Attendance (${attendance.size})") {
            attendance.forEach { record ->
                Column(modifier = Modifier.padding(vertical = 6.dp)) {
                    Text(record.Name, fontWeight = FontWeight.SemiBold)
                    Text("${record.Date} | IN ${record.CheckIn} | OUT ${record.CheckOut}")
                    Text("Hours: ${record.WorkHours.ifBlank { "-" }}")
                }
                Divider()
            }
        }

        Spacer(modifier = Modifier.height(12.dp))
    }
}

@Composable
private fun SectionCard(title: String, content: @Composable androidx.compose.foundation.layout.ColumnScope.() -> Unit) {
    Card(
        colors = CardDefaults.cardColors(),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            content()
        }
    }
}
