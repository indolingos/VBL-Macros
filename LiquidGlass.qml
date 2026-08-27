import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects

ApplicationWindow {
    id: window
    visible: true
    width: 720
    height: 860
    minimumWidth: 620
    minimumHeight: 740
    title: "VBL Macro"
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.Window

    property real mx: width / 2
    property real my: height / 2
    property real focusGlow: backend.robloxFocused ? 1.0 : 0.0
    property real glassShift: 0

    onWidthChanged: { mx = width / 2 }
    onHeightChanged: { my = height / 2 }

    Timer {
        interval: 16
        repeat: true
        running: true
        onTriggered: window.glassShift = (window.glassShift + 0.7) % 360
    }

    Rectangle {
        anchors.fill: parent
        color: "#0b0d12"
        radius: 28
        antialiasing: true
    }

    Item {
        anchors.fill: parent
        clip: true

        Rectangle {
            id: glowA
            width: 390; height: 390; radius: width / 2
            x: -110 + Math.sin(window.glassShift / 50) * 22
            y: -100 + Math.cos(window.glassShift / 65) * 18
            color: "#8F76FF"
            opacity: 0.16
            layer.enabled: true
            layer.effect: MultiEffect { blurEnabled: true; blur: 1.0; blurMax: 64 }
        }
        Rectangle {
            width: 440; height: 440; radius: width / 2
            x: window.width - 210 + Math.cos(window.glassShift / 55) * 20
            y: 70 + Math.sin(window.glassShift / 70) * 22
            color: "#55D8FF"
            opacity: 0.13
            layer.enabled: true
            layer.effect: MultiEffect { blurEnabled: true; blur: 1.0; blurMax: 64 }
        }
        Rectangle {
            width: 500; height: 500; radius: width / 2
            x: window.width * 0.38
            y: window.height - 240 + Math.sin(window.glassShift / 80) * 20
            color: "#6C8FFF"
            opacity: 0.10
            layer.enabled: true
            layer.effect: MultiEffect { blurEnabled: true; blur: 1.0; blurMax: 64 }
        }
    }

    Rectangle {
        id: sheet
        anchors.fill: parent
        anchors.margins: 14
        radius: 24
        color: "#B8181B22"
        border.width: 1
        border.color: "#43FFFFFF"
        antialiasing: true

        layer.enabled: true
        layer.effect: MultiEffect {
            shadowEnabled: true
            shadowBlur: 26
            shadowOpacity: 0.55
            shadowVerticalOffset: 10
            shadowColor: "#000000"
        }
    }

    Rectangle {
        anchors.fill: sheet
        anchors.margins: 1
        radius: sheet.radius - 1
        color: "transparent"
        border.width: 1
        border.color: "#25FFFFFF"
        antialiasing: true
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        hoverEnabled: true
        onPositionChanged: function(mouse) {
            window.mx = mouse.x
            window.my = mouse.y
        }
        onPressed: function(mouse) {
            window.startSystemMove()
        }
    }

    RowLayout {
        id: header
        anchors.left: sheet.left
        anchors.right: sheet.right
        anchors.top: sheet.top
        anchors.margins: 24
        height: 46
        spacing: 12

        Item { Layout.fillWidth: true; Layout.fillHeight: true }

        Rectangle {
            width: 104; height: 32; radius: 16
            color: backend.running ? "#267BE7B0" : "#20FFFFFF"
            border.color: backend.running ? "#557BE7B0" : "#22FFFFFF"
            border.width: 1
            Row {
                anchors.centerIn: parent
                spacing: 7
                Rectangle { width: 7; height: 7; radius: 3.5; color: backend.running ? "#7BE7B0" : "#9CA2AE"; anchors.verticalCenter: parent.verticalCenter }
                Text { text: backend.running ? "ONLINE" : "OFFLINE"; color: backend.running ? "#A5F2C8" : "#D3D6DD"; font.pixelSize: 10; font.bold: true }
            }
        }

        Rectangle {
            width: 34; height: 34; radius: 17; color: "#16FFFFFF"; border.color: "#28FFFFFF"; border.width: 1
            Text { anchors.centerIn: parent; text: "—"; color: "#D6D9E0"; font.pixelSize: 15 }
            MouseArea { anchors.fill: parent; onClicked: backend.minimize() }
        }
        Rectangle {
            width: 34; height: 34; radius: 17; color: "#16FFFFFF"; border.color: "#28FFFFFF"; border.width: 1
            Text { anchors.centerIn: parent; text: "□"; color: "#D6D9E0"; font.pixelSize: 13 }
            MouseArea { anchors.fill: parent; onClicked: backend.maximize() }
        }
        Rectangle {
            width: 34; height: 34; radius: 17; color: "#16FFFFFF"; border.color: "#28FFFFFF"; border.width: 1
            Text { anchors.centerIn: parent; text: "×"; color: "#D6D9E0"; font.pixelSize: 17 }
            MouseArea { anchors.fill: parent; onClicked: backend.quit() }
        }
    }

    ColumnLayout {
        anchors.left: sheet.left
        anchors.right: sheet.right
        anchors.top: header.bottom
        anchors.bottom: sheet.bottom
        anchors.margins: 24
        anchors.topMargin: 18
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            spacing: 14
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text { text: "VBL"; color: "#F7F8FB"; font.pixelSize: 12; font.bold: true; opacity: 0.82 }
                Text { text: "Macro"; color: "#FFFFFF"; font.pixelSize: 30; font.bold: true }
                Text { text: "INPUT AUTOMATION"; color: "#A9AFBB"; font.pixelSize: 9 }
            }
            Rectangle {
                Layout.preferredWidth: 250; Layout.preferredHeight: 42; radius: 21
                color: backend.robloxFocused ? "#247BE7B0" : "#1AFFFFFF"
                border.width: 1
                border.color: backend.robloxFocused ? "#667BE7B0" : "#25FFFFFF"
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 14
                    spacing: 9
                    Rectangle { width: 8; height: 8; radius: 4; color: backend.robloxFocused ? "#7BE7B0" : "#FF7186" }
                    Text { text: backend.robloxFocused ? "ROBLOX  •  FOCUSED" : "ROBLOX  •  NOT FOCUSED"; color: backend.robloxFocused ? "#B5F4D0" : "#FFC2C9"; font.pixelSize: 9; font.bold: true; Layout.fillWidth: true }
                }
            }
        }

        Rectangle {
            id: hero
            Layout.fillWidth: true
            Layout.preferredHeight: 238
            radius: 26
            color: "#1AFFFFFF"
            border.width: 1
            border.color: backend.running ? "#4A7BE7B0" : "#2DFFFFFF"
            antialiasing: true

            Rectangle {
                anchors.fill: parent
                anchors.margins: 1
                radius: parent.radius - 1
                color: "transparent"
                border.width: 1
                border.color: "#10FFFFFF"
            }

            RowLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20

                Item {
                    Layout.preferredWidth: 160
                    Layout.fillHeight: true
                    Item {
                        anchors.centerIn: parent
                        width: 150; height: 150
                        transformOrigin: Item.Center
                        Rectangle { anchors.centerIn: parent; width: 122; height: 122; radius: 61; color: backend.running ? "#277BE7B0" : "#15FFFFFF"; opacity: 0.32; layer.enabled: true; layer.effect: MultiEffect { blurEnabled: true; blur: 1; blurMax: 30 } }
                        Rectangle { anchors.centerIn: parent; width: 94; height: 94; radius: 47; color: "#1CFFFFFF"; border.color: backend.running ? "#887BE7B0" : "#34FFFFFF"; border.width: 1 }
                        Rectangle { anchors.centerIn: parent; width: 72; height: 72; radius: 36; color: backend.running ? "#587BE7B0" : "#18252A34" }
                        Rectangle { anchors.centerIn: parent; width: 20; height: 20; radius: 10; color: "#FFFFFF"; opacity: backend.running ? 1 : 0.92 }
                        Rectangle { anchors.centerIn: parent; width: 5; height: 5; radius: 2.5; color: backend.running ? "#7BE7B0" : "#A4AAB4" }
                    }
                    Text { anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; text: backend.running ? (backend.robloxFocused ? "LIVE" : "WAITING") : "STANDBY"; color: backend.running ? (backend.robloxFocused ? "#A6F4C8" : "#FFE28C") : "#AEB4BF"; font.pixelSize: 9; font.bold: true }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 5
                    Text { text: "ENGINE STATUS"; color: "#9FA5B0"; font.pixelSize: 9; font.bold: true }
                    Text { text: backend.running ? (backend.robloxFocused ? "INPUT LIVE" : "WAITING FOR ROBLOX") : "READY"; color: "#F8F9FC"; font.pixelSize: 24; font.bold: true }
                    Text { text: backend.running ? "Focus lock is protecting your input." : "Arm the macro whenever you are ready."; color: "#AAB0BA"; font.pixelSize: 10 }
                    Item { Layout.fillHeight: true }
                    Rectangle {
                        Layout.fillWidth: true; Layout.preferredHeight: 58; radius: 19
                        color: backend.running ? "#237BE7B0" : "#14FFFFFF"
                        border.width: 1; border.color: backend.running ? "#667BE7B0" : "#20FFFFFF"
                        Text { anchors.centerIn: parent; text: backend.running ? "STOP MACRO" : "START MACRO"; color: "#FFFFFF"; font.pixelSize: 12; font.bold: true }
                        MouseArea { anchors.fill: parent; onClicked: backend.toggle() }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 126; radius: 24
            color: "#16FFFFFF"; border.width: 1; border.color: "#25FFFFFF"
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 16; spacing: 9
                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "COMBO PROFILES"; color: "#A5ABB5"; font.pixelSize: 9; font.bold: true }
                    Item { Layout.fillWidth: true }
                    Text { text: "LIVE PIPELINE"; color: "#91DFFF"; font.pixelSize: 8; font.bold: true }
                }
                RowLayout {
                    Layout.fillWidth: true; spacing: 10
                    Repeater {
                        model: [
                            { key: "`", text: "RMB", sub: "SPACE", end: "LMB", color: "#78DFFF" },
                            { key: "R", text: "RMB", sub: "SPACE", end: "", color: "#BBA1FF" }
                        ]
                        delegate: Rectangle {
                            Layout.fillWidth: true; Layout.preferredHeight: 56; radius: 18
                            color: "#12FFFFFF"; border.width: 1; border.color: "#18FFFFFF"
                            RowLayout { anchors.fill: parent; anchors.margins: 12; spacing: 9
                                Rectangle { width: 34; height: 34; radius: 11; color: modelData.color; Text { anchors.centerIn: parent; text: modelData.key; color: "#14161B"; font.pixelSize: 13; font.bold: true } }
                                ColumnLayout { spacing: 1; Layout.fillWidth: true
                                    Text { text: modelData.text + "  →  " + modelData.sub + (modelData.end !== "" ? "  →  " + modelData.end : ""); color: "#EEF0F5"; font.pixelSize: 9; font.bold: true }
                                    Text { text: modelData.end !== "" ? "3-STEP PROFILE" : "2-STEP PROFILE"; color: modelData.color; font.pixelSize: 7; font.bold: true }
                                }
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true; Layout.fillHeight: true; radius: 24
            color: "#16FFFFFF"; border.width: 1; border.color: "#25FFFFFF"
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 16; spacing: 10
                RowLayout { Layout.fillWidth: true
                    Text { text: "SESSION"; color: "#A5ABB5"; font.pixelSize: 9; font.bold: true }
                    Item { Layout.fillWidth: true }
                    Text { text: backend.running ? backend.uptime : "00:00:00"; color: "#E9EBF1"; font.pixelSize: 10; font.bold: true }
                }
                RowLayout { Layout.fillWidth: true; spacing: 8
                    Repeater {
                        model: [
                            { title: "FIRES", value: backend.eventCount, color: "#78DFFF" },
                            { title: "LAST KEY", value: backend.lastKey, color: "#BBA1FF" },
                            { title: "LAST TIME", value: backend.lastTime, color: "#86A6FF" },
                            { title: "UPTIME", value: backend.uptime, color: "#7BE7B0" }
                        ]
                        delegate: Rectangle {
                            Layout.fillWidth: true; Layout.preferredHeight: 60; radius: 17
                            color: "#12FFFFFF"; border.width: 1; border.color: "#15FFFFFF"
                            Column { anchors.fill: parent; anchors.margins: 10; spacing: 3
                                Text { text: modelData.title; color: "#898F9B"; font.pixelSize: 7; font.bold: true }
                                Text { text: modelData.value; color: "#F5F6FA"; font.pixelSize: 14; font.bold: true }
                            }
                        }
                    }
                }
                Text { text: "ACTIVITY"; color: "#A5ABB5"; font.pixelSize: 8; font.bold: true }
                Rectangle {
                    Layout.fillWidth: true; Layout.fillHeight: true; radius: 18
                    color: "#0E000000"; border.width: 1; border.color: "#15FFFFFF"
                    Text { anchors.centerIn: parent; text: "Ready for macro activity"; color: "#686F7B"; font.pixelSize: 9 }
                }
            }
        }
    }

    Connections {
        target: backend
        function onToast(message, color) {
            toastText.text = message
            toastText.color = color
            toastText.opacity = 1
            toastTimer.restart()
        }
    }

    Rectangle {
        id: toastBubble
        visible: toastText.opacity > 0
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: sheet.bottom
        anchors.bottomMargin: 18
        width: Math.max(170, toastText.implicitWidth + 34)
        height: 38
        radius: 19
        color: "#D51C2028"
        border.width: 1
        border.color: "#35FFFFFF"
        Text { id: toastText; anchors.centerIn: parent; text: ""; color: "#FFFFFF"; font.pixelSize: 9; font.bold: true; opacity: 0 }
        Timer { id: toastTimer; interval: 1200; onTriggered: toastText.opacity = 0 }
        Behavior on opacity { NumberAnimation { duration: 160 } }
    }
}
