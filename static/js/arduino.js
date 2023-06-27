const states = [
	{ state: E_OK, color: "#A6E22E" },
	{ state: E_NOK, color: "red" },
]

var accState = E_NOK
var wdState = E_NOK
var ignState = E_NOK
var opt2State = E_NOK

const ArduinoRelayButton = [
	{ button: "acc_button", label: "acc_label", state: accState },
	{ button: "ign_button", label: "ign_label", state: ignState },
	{ button: "opt2_button", label: "opt2_label", state: opt2State },
	{ button: "wd_button", label: "wd_label", state: wdState },
]
function monitorArduinoRelayButtonClick(button) {
	const buttonElement = $("#" + button.button)
	buttonElement.on("click", function () {
		button.state = !button.state

		fetch(`/turn/${button.button}/${button.state == true ? 0 : 1}`, {
			method: "GET",
		})
			.then((response) => response.json())
			.then((data) => {
				syncData(data.message)
			})
			.catch((error) => {
				console.error("Error:", error)
			})
	})
}

function syncData(data) {
	if (data.includes("Arduino not CONNECTED")) {
		$("#status").text(data)
	} else {
		for (let i = 0; i < 4; i++) {
			let button = ArduinoRelayButton[i].button.split("_")[0]
			let state = parseInt(data[i]) === 0 ? E_OK : E_NOK
			ArduinoRelayButton[i].state = state
			let payload = {
				button: button,
				response: state,
			}
			setArduinoRelayButtonStateAndColor(payload)
		}
	}
}

function setArduinoRelayButtonStateAndColor(response) {
	// console.log(response)
	let buttonName = response.button
	let responseState = response.response
	const matchingState = states.find((state) => state.state === responseState)
	if (matchingState) {
		$("#" + buttonName + "_button, #" + buttonName + "_label").css(
			"color",
			matchingState.color,
		)
	}
}
