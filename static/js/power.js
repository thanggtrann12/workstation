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
				socket.emit(`set_power_to_${button.state == E_OK ? "on" : "off"}`)
			} else {
				console.log(button.button)
				let voltage = parseInt($("#input_voltage").val())
				if (voltage > 0) {
					payload = { voltage: voltage, current: 0 }
					socket.emit("update_data_to_toellner", (data = payload))
				}
			}
		}
	})
}

function setCurrentPowerState(state) {
	if (state === "power_off" || state === "stand_by") {
		powerState = E_NOK
		$("#" + PowerButtons[0].button + ", #" + PowerButtons[0].label).css(
			"color",
			"#RED",
		)
		$("#" + PowerButtons[0].button).text("OFF")
	}
	if (state === "power_on" || state === "normal") {
		$("#" + PowerButtons[0].button + ", #" + PowerButtons[0].label).css(
			"color",
			"#A6E22E",
		)
		$("#" + PowerButtons[0].button).text("ON")
		powerState = E_OK
	}
	setTargetStatus(state)
}
