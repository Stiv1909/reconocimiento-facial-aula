import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    width: 1000
    height: 650
    title: "Interfaz Administrativa - Institución Educativa del Sur"
    color: "#121212" // Tema oscuro

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 10

        // Encabezado
        RowLayout {
            spacing: 20
            Image {
                source: "logo_institucion.jpeg"
                width: 70; height: 70
                fillMode: Image.PreserveAspectFit
            }
            ColumnLayout {
                spacing: 4
                Text { text: "Institución Educativa del Sur"; font.pixelSize: 32; font.bold: true; color: "#E3F2FD" }
                Text { text: "Compromiso y Superación"; font.pixelSize: 18; color: "#aaa" }
            }
            Item { Layout.fillWidth: true }
            Button {
                background: Rectangle { color: "#C62828"; radius: 6 }
                contentItem: Text { text: qsTr("CREAR SESIÓN"); color: "white"; font.bold: true; anchors.centerIn: parent }
            }
            Button {
                background: Rectangle { color: "#1565C0"; radius: 6 }
                contentItem: Text { text: qsTr("MÁS INFORMACIÓN"); color: "white"; font.bold: true; anchors.centerIn: parent }
            }
        }

        Rectangle { height: 1; color: "#444"; Layout.fillWidth: true }

        // Títulos
        Text { text: "Sistema de gestión de equipos"; font.pixelSize: 28; font.bold: true; color: "#E3F2FD"; horizontalAlignment: Text.AlignHCenter; Layout.alignment: Qt.AlignHCenter }
        Text { text: "Por favor seleccione la acción que desea realizar"; font.pixelSize: 16; color: "#ccc"; horizontalAlignment: Text.AlignHCenter; Layout.alignment: Qt.AlignHCenter }

        // Grid de acciones
        GridLayout {
            columns: 5
            rowSpacing: 25
            columnSpacing: 25
            Layout.fillWidth: true
            Layout.fillHeight: true

            Repeater {
                model: [
                    { name: "Registrar Docente",         icon: "icons/docente.png",     color: "#1565C0" },
                    { name: "Dar Ingreso a Estudiantes", icon: "icons/ingreso.png",     color: "#2E7D32" },
                    { name: "Dar Salida a Estudiantes",  icon: "icons/salida.png",      color: "#2E7D32" },
                    { name: "Editar Estudiantes",        icon: "icons/editar_est.png",  color: "#2E7D32" },
                    { name: "Registrar Estudiantes",     icon: "icons/estudiante.png",  color: "#2E7D32" },
                    { name: "Gestionar Equipos",         icon: "icons/equipos.png",     color: "#EF6C00" },
                    { name: "Registrar Incidente",       icon: "icons/incidente.png",   color: "#C62828" },
                    { name: "Consultar Historial de Accesos", icon: "icons/listar.png", color: "#EF6C00" },
                    { name: "Generación de Asistencia",  icon: "icons/asis.png",        color: "#2E7D32" }
                ]

                delegate: Flipable {
                    width: 150
                    height: 120
                    property bool flipped: false

                    // Sombra simulada
                    Rectangle {
                        anchors.fill: parent
                        radius: 15
                        color: "transparent"
                        border.color: "transparent"
                        z: -1
                        anchors.margins: -6
                        opacity: 0.2
                    }

                    // Cara frontal
                    front: Rectangle {
                        id: frontCard
                        anchors.fill: parent
                        radius: 15
                        color: "#ffffff15"
                        border.color: model.color
                        border.width: 2
                        clip: true

                        // Bordes iluminados
                        Rectangle {
                            anchors.fill: parent; radius: parent.radius
                            border.width: 0
                            gradient: Gradient {
                                GradientStop { position: 0.0; color: "#ffffff30" }
                                GradientStop { position: 0.1; color: "transparent" }
                                GradientStop { position: 0.9; color: "transparent" }
                                GradientStop { position: 1.0; color: "#ffffff15" }
                            }
                            opacity: 0.8
                        }

                        // Brillo diagonal animado
                        Rectangle {
                            id: shine
                            width: frontCard.width * 1.6
                            height: frontCard.height * 1.6
                            rotation: 45
                            x: -width; y: -height/3
                            gradient: Gradient {
                                GradientStop { position: 0.0; color: "transparent" }
                                GradientStop { position: 0.48; color: "#ffffff00" }
                                GradientStop { position: 0.5; color: "#ffffff44" }
                                GradientStop { position: 0.52; color: "#ffffff00" }
                                GradientStop { position: 1.0; color: "transparent" }
                            }
                            opacity: 0.0

                            SequentialAnimation on x {
                                loops: Animation.Infinite
                                NumberAnimation { from: -shine.width; to: frontCard.width; duration: 2500; easing.type: Easing.InOutSine }
                                PauseAnimation { duration: 1000 }
                            }
                        }

                        Column {
                            anchors.centerIn: parent
                            spacing: 8
                            Image { source: model.icon; width: 44; height: 44; fillMode: Image.PreserveAspectFit }
                            Text {
                                text: model.name
                                font.pixelSize: 12
                                color: "white"
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.WordWrap
                                width: parent.width * 0.9
                            }
                        }
                    }

                    // Cara trasera
                    back: Rectangle {
                        anchors.fill: parent
                        radius: 15
                        color: "#1E1E1E"
                        border.color: model.color
                        border.width: 2

                        Text {
                            anchors.centerIn: parent
                            text: "Abrir: " + model.name
                            color: "white"
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                            width: parent.width * 0.9
                        }
                    }

                    // Rotación
                    transform: Rotation {
                        origin.x: width / 2
                        origin.y: height / 2
                        axis.y: 1
                        angle: flipped ? 180 : 0
                        Behavior on angle { NumberAnimation { duration: 260; easing.type: Easing.InOutQuad } }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true

                        onEntered: {
                            frontCard.opacity = 0.95
                            shine.opacity = 0.7
                        }

                        onExited: {
                            frontCard.opacity = 1.0
                            shine.opacity = 0.0
                        }

                        onClicked: {
                            flipped = true
                            // Delay para completar el flip y abrir ventana Python
                            Qt.createQmlObject(
                                'import QtQuick 2.15; Timer { interval: 260; repeat: false; onTriggered: { flipped = false; backend.abrirVentana(model.name) } }',
                                parent,
                                "FlipTimer"
                            ).start()
                        }
                    }
                }
            }
        }
    }
}
