$(document).ready(function () {
	$("#command_entry").on("input", function () {
		ttfis_cmd = $(this).val().toUpperCase()
	})
	$("#command_entry").on("keydown", function (event) {
		doAutoComplete(event)
	})
	$("#standby_buton").on("click", function () {
		$("#scc_trace").empty()
		standby_test()
	})
	$("#shutdown_buton").on("click", function () {
		$("#scc_trace").empty()
		shutdown_test()
	})
	$("#set_test_time").on("click", () => {
		setTestTime()
	})
	$("#record_scc").change(function () {
		if (this.checked) {
			isRecording = true
		} else {
			isRecording = false
			var fileName = `recorded_text_${new Date().toISOString()}.pro`
			var blob = new Blob([recordedText], {
				type: "text/plain;charset=utf-8",
			})
			saveAs(blob, fileName)
		}
	})

	$("#pause_scc").change(function () {
		if (this.checked) {
			isPausing = true
		} else {
			isPausing = false
		}
	})

	$("#clear_scc").click(function () {
		$("#scc_trace").empty()
	})

	$("#export_scc").click(function () {
		console.log("export")
		{
			const text = $("#scc_trace").text()
			let blob = new Blob([text], {
				type: "text/plain",
			})
			let filename = `${new Date().toISOString()}_SCC_Log.pro`
			saveAs(blob, filename)
		}
	})

	ArduinoRelayButton.forEach(monitorArduinoRelayButtonClick)
	TargetButtons.forEach(monitorTargetbuttonsClick)
	PowerButtons.forEach(monitorPowerButtonsClick)
})
