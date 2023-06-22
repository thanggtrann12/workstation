$(document).ready(function () {
	$("#command_entry").on("input", function () {
		ttfis_cmd = $(this).val().toUpperCase()
	})
	$("#command_entry").on("keydown", function (event) {
		doAutoComplete(event)
	})
	$("#standby_buton").on("click", async function () {
		$("#acc_button , #acc_label, #ign_button, #ign_label").css(
			"color",
			"red",
		)
		$("#scc_trace").empty()
		try {
			await $.get(
				"http://" +
					location.host +
					`/start-test/standby/${
						$("#test_time").val() == ""
							? 1
							: parseInt($("#test_time").val())
					}`,
			)
		} catch (error) {
			console.error("Error occurred during the GET request:", error)
		}
	})
	$("#shutdown_buton").on("click", async function () {
		$("#scc_trace").empty()
		$("#acc_button , #acc_label, #ign_button, #ign_label").css(
			"color",
			"red",
		)
		try {
			await $.get(
				"http://" +
					location.host +
					`/start-test/shutdown/${
						$("#test_time").val() == ""
							? 1
							: parseInt($("#test_time").val())
					}`,
			)
		} catch (error) {
			console.error("Error occurred during the GET request:", error)
		}
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
