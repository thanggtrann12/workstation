var powerState = E_NOK
let power_state = ""
const PowerButtons = [
	{ button: "power_button", label: "power_label", state: powerState },
	{ button: "set_voltage_button", label: "SET", state: "" },
]
function monitorPowerButtonsClick(button) {
	const buttonElement = $("#" + button.button)
	buttonElement.on("click", function () {
		{
			if (button.label !== "SET") {
				button.state = !button.state
				fetch("/power", {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
					},
					body: JSON.stringify({ state: button.state }),
				})
					.then((response) => response.json())
					.then((data) => {
						setPowerState(data.message)
					})

					.catch((error) => {
						console.error("Error:", error)
					})
			} else {
				let voltage = parseInt($("#input_voltage").val())

				payload = { voltage: voltage, current: 0 }
				socket.emit("update_data_to_toellner", (data = payload))
				$("#input_voltage").val("")
			}
		}
	})
}

function setPowerState(state) {
	if (state.includes("OFF")) {
		$("#" + PowerButtons[0].button + ", #" + PowerButtons[0].label).css(
			"color",
			"red",
		)
		PowerButtons[0].state = false
	} else if (state.includes("ON")) {
		{
			$("#" + PowerButtons[0].button + ", #" + PowerButtons[0].label).css(
				"color",
				"#A6E22E",
			)
		}
		PowerButtons[0].state = true
	}

	$("#" + PowerButtons[0].button).text(state)
}

function updataPowerData(data) {
	let voltage = data.voltage
	let current = data.current
	$("#voltage").text(voltage)
	$("#current").text(current)
	if (voltage > 0 && current > 0) {
		setTargetStatus("normal")
	}
	if (voltage > 0 && current == 0) {
		setTargetStatus("stand_by")
	}
	if (voltage == 0) {
		setTargetStatus("power_off")
	}
}
