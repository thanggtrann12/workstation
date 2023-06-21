const TargetButtons = [
	{ pin: "flash_button", action: () => uploadFile("#file-dnl-input") },
	{ pin: "upload_trace_button", action: () => uploadFile("#file-trc-input") },
]

function uploadFile(fileInputId) {
	console.log(fileInputId)
	try {
		var fileData = $(fileInputId).prop("files")[0]
		if (!fileData) {
			$("#status").text("Files is empty")
			return
		}
		var formData = new FormData()
		formData.append(fileInputId.substring(1), fileData)
		$.ajax({
			url: "/upload",
			type: "POST",
			data: formData,
			processData: false,
			contentType: false,
			success: function (response) {},
		})
	} catch {
		console.log("error")
	}
}

function monitorTargetbuttonsClick(button) {
	const buttonElement = $("#" + button.pin)
	buttonElement.on("click", function () {
		button.action() // Call the action function
	})
}
let target_status = E_NOK
function setTargetStatus(status) {
	target_status = status
	if (status !== "normal") {
		$("#target_status").css("color", "red")
		target_status = E_NOK
	} else {
		target_status = E_OK
		$("#target_status").css("color", "#A6E22E")
	}
	$("#target_status").text(status.split("_").join("").toUpperCase())
}

function getTargetStatus() {
	console.log(target_status)
	return target_status
}

function setTargetWakeup() {
	socket.emit("set_tartget_wakeup")
}
function setTargetPowerDown() {
	console.log("set_power_to_off")
	socket.emit("set_power_to_off")
}
function setTargetPowerUp() {
	console.log("set_power_to_on")
	socket.emit("set_power_to_on")
}
