import QtQuick
import QtQuick.Window

Window {
    id: overlay
    objectName: "robloxOverlay"
    visible: backend.running
    width: 360
    height: 92
    x: 24
    y: Screen.height - height - 92
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus | Qt.WindowTransparentForInput
    title: "VBL Macro Overlay"

    property real pulse: 0
    property color accent: backend.running ? (backend.robloxFocused ? "#79E7B0" : "#FFD86F") : "#A7ADB8"

    NumberAnimation on pulse {
        from: 0
        to: 1
        duration: 1800
        loops: Animation.Infinite
        easing.type: Easing.InOutSine
        running: true
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 3
        radius: 28
        color: "#C8141820"
        border.width: 1
        border.color: "#45FFFFFF"
        antialiasing: true

        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            radius: parent.radius - 1
            color: "transparent"
            border.width: 1
            border.color: "#18FFFFFF"
        }

        Rectangle {
            x: 18
            y: 7
            width: parent.width - 36
            height: 1
            color: "#55FFFFFF"
            opacity: 0.5
        }

        Row {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.rightMargin: 18
            spacing: 14

            Item {
                width: 46
                height: parent.height

                Rectangle {
                    anchors.centerIn: parent
                    width: 38 + overlay.pulse * 5
                    height: width
                    radius: width / 2
                    color: overlay.accent
                    opacity: 0.11
                }

                Rectangle {
                    anchors.centerIn: parent
                    width: 28
                    height: 28
                    radius: 14
                    color: "#21FFFFFF"
                    border.width: 1
                    border.color: overlay.accent

                    Rectangle {
                        anchors.centerIn: parent
                        width: 9
                        height: 9
                        radius: 4.5
                        color: overlay.accent
                    }
                }
            }

            Column {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 3

                Row {
                    spacing: 8
                    Text {
                        text: "VBL MACRO"
                        color: "#F7F8FC"
                        font.pixelSize: 12
                        font.bold: true
                    }
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 7
                        height: 7
                        radius: 3.5
                        color: overlay.accent
                    }
                }

                Text {
                    text: backend.running
                        ? (backend.robloxFocused ? "LIVE  •  ROBLOX FOCUSED" : "ARMED  •  WAITING FOR ROBLOX")
                        : "MACRO DISARMED"
                    color: overlay.accent
                    font.pixelSize: 9
                    font.bold: true
                }

                Text {
                    text: backend.running
                        ? (backend.robloxFocused ? "Hotkeys ready  •  ` + R" : "Focus Roblox to enable input")
                        : "Start the macro from VBL Macro"
                    color: "#A9AFBA"
                    font.pixelSize: 8
                }
            }

            Item { width: 1; height: 1 }

            Column {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 2
                Text {
                    text: backend.eventCount
                    color: "#F6F7FB"
                    font.pixelSize: 17
                    font.bold: true
                    horizontalAlignment: Text.AlignRight
                }
                Text {
                    text: "FIRES"
                    color: "#858C99"
                    font.pixelSize: 7
                    font.bold: true
                }
            }
        }
    }
}
