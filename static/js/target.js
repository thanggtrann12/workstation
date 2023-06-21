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
		console.log("button click")
		button.action() // Call the action function
	})
}
