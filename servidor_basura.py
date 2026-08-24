from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# Diccionario dinámico: vació al arrancar, se llena conforme los camiones transmiten
vehiculos_estado = {}

# 1. INTERFAZ DEL CLIENTE (VECINOS) - Se ve en la raíz "/"
@app.route('/')
def cliente_mapa():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ruta Basura en Vivo - ATA Ingeniería</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
        <style>
            body { margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; height: 100vh; overflow: hidden; }
            #sidebar { width: 360px; height: 100vh; background: #f8f9fa; box-shadow: 2px 0 5px rgba(0,0,0,0.1); z-index: 1000; padding: 15px; box-sizing: border-box; overflow-y: auto; flex-shrink: 0; }
            #map { flex-grow: 1; height: 100vh; }
            h2 { font-size: 18px; color: #2c3e50; margin-top: 0; margin-bottom: 8px; }
            .instructions { font-size: 12px; color: #666; margin-bottom: 12px; line-height: 1.4; }
            .instructions b { color: #28a745; }
            .route-btn { display: block; width: 100%; padding: 12px; margin-bottom: 8px; background: #ffffff; border: 2px solid #e9ecef; border-radius: 8px; text-align: left; cursor: pointer; font-size: 13px; transition: all 0.2s ease; font-weight: 600; color: #333; }
            .route-btn:hover { background: #e8f5e9; border-color: #28a745; color: #2e7d32; }
            .route-btn.active { background: #c8e6c9; border-color: #2e7d32; color: #1b5e20; }
            .route-btn span { display: block; font-size: 11px; color: #666; font-weight: normal; margin-top: 3px; }
            .btn-gps-usuario { background: #007bff; color: white; border: none; width: 100%; padding: 10px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-bottom: 12px; font-size: 13px; }
            .btn-gps-usuario:hover { background: #0056b3; }
            .status-card { margin-top: 10px; padding: 12px; background: #e8f4ff; border-radius: 8px; font-size: 12px; color: #004085; line-height: 1.5; border-left: 4px solid #007bff; }
            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
            .live-indicator { display: inline-block; width: 8px; height: 8px; background: #28a745; border-radius: 50%; margin-right: 5px; animation: pulse 1.5s infinite; }
            @media (max-width: 768px) {
                body { flex-direction: column-reverse; }
                #sidebar { width: 100%; height: 45vh; padding: 12px; box-shadow: 0 -2px 10px rgba(0,0,0,0.15); }
                #map { width: 100%; height: 55vh; }
            }
        </style>
    </head>
    <body>
        <div id="sidebar">
            <h2>🚚 Rutas de Recolección</h2>
            <p class="instructions"><b>Selecciona una ruta</b> para ver todos los camiones activos en tiempo real.</p>
            <button class="btn-gps-usuario" onclick="ubicarCliente()">📍 Ubicar mi posición / Casa</button>

            <div id="contenedor-rutas">
                <button class="route-btn" onclick="seleccionarRuta('ruta_centro', 'Ruta Centro')">
                    🚛 Ruta Centro
                    <span>Muestra todos los camiones en esta zona</span>
                </button>
                <button class="route-btn" onclick="seleccionarRuta('ruta_norte', 'Ruta Norte')">
                    🚛 Ruta Norte
                    <span>Muestra todos los camiones en esta zona</span>
                </button>
                <button class="route-btn" onclick="seleccionarRuta('ruta_sur', 'Ruta Sur')">
                    🚛 Ruta Sur
                    <span>Muestra todos los camiones en esta zona</span>
                </button>
            </div>

            <div id="panel-estado" class="status-card" style="display:none;">
                <b><span class="live-indicator"></span>Monitoreando:</b> <span id="lbl-ruta-actual">Ninguna</span><br>
                🚛 <b>Unidades en vivo:</b> <span id="lbl-coor">Buscando...</span><br>
                📏 <b>Distancia más cercana:</b> <span id="lbl-distancia-usuario" style="color: #d9534f; font-weight: bold;">Activa "Ubicar mi posición"</span>
            </div>
        </div>

        <div id="map"></div>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
        <script>
            const map = L.map('map').setView([5.3377, -72.3961], 15);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap - ATA' }).addTo(map);

            let rutaActivaId = null;
            let marcadorUsuario = null;
            let posicionUsuarioCoords = null;
            let intervaloConsulta = null;
            let marcadoresVehiculos = {}; 
            let polylinesVehiculos = {};

            const iconoCamion = L.divIcon({
                className: 'custom-camion-icon',
                html: '<div style="background:#28a745; color:white; padding:4px; border-radius:50%; font-size:14px; box-shadow:0 3px 10px rgba(0,0,0,0.4); text-align:center; width:24px; height:24px; display:flex; align-items:center; justify-content:center;">🚛</div>',
                iconSize: [32, 32], iconAnchor: [16, 16]
            });

            const iconoUsuario = L.divIcon({
                className: 'custom-user-icon',
                html: '<div style="background:#007bff; color:white; padding:4px; border-radius:50%; font-size:14px; box-shadow:0 3px 10px rgba(0,0,0,0.4); text-align:center; width:24px; height:24px; display:flex; align-items:center; justify-content:center;">🏠</div>',
                iconSize: [32, 32], iconAnchor: [16, 16]
            });

            function ubicarCliente() {
                if (!navigator.geolocation) return alert("Sin soporte de GPS.");
                navigator.geolocation.getCurrentPosition((pos) => {
                    posicionUsuarioCoords = [pos.coords.latitude, pos.coords.longitude];
                    if (!marcadorUsuario) {
                        marcadorUsuario = L.marker(posicionUsuarioCoords, { icon: iconoUsuario }).addTo(map).bindPopup("<b>Mi Casa</b>").openPopup();
                    } else {
                        marcadorUsuario.setLatLng(posicionUsuarioCoords);
                    }
                    alert("¡Casa ubicada con éxito!");
                    consultarPosicionRuta();
                }, () => alert("No se pudo obtener la ubicación."), { enableHighAccuracy: true });
            }

            function seleccionarRuta(idRuta, nombreRuta) {
                document.querySelectorAll('.route-btn').forEach(btn => btn.classList.remove('active'));
                event.currentTarget.classList.add('active');
                document.getElementById('panel-estado').style.display = 'block';
                document.getElementById('lbl-ruta-actual').textContent = nombreRuta;

                if (intervaloConsulta) clearInterval(intervaloConsulta);

                for (let id in marcadoresVehiculos) map.removeLayer(marcadoresVehiculos[id]);
                for (let id in polylinesVehiculos) map.removeLayer(polylinesVehiculos[id]);
                marcadoresVehiculos = {};
                polylinesVehiculos = {};

                rutaActivaId = idRuta;
                consultarPosicionRuta();
                intervaloConsulta = setInterval(consultarPosicionRuta, 3000);
            }

            async function consultarPosicionRuta() {
                if (!rutaActivaId) return;
                try {
                    const res = await fetch('/api/obtener-vehiculos');
                    const vehiculos = await res.json();

                    let elementosZoom = [];
                    if (marcadorUsuario) elementosZoom.push(marcadorUsuario);

                    let activosCount = 0;
                    let menorDist = 9999999;

                    for (let id in vehiculos) {
                        const v = vehiculos[id];
                        if (v.ruta === rutaActivaId && v.historial && v.historial.length > 0) {
                            activosCount++;
                            const ultimaPos = v.historial[v.historial.length - 1];

                            if (!marcadoresVehiculos[id]) {
                                marcadoresVehiculos[id] = L.marker(ultimaPos, { icon: iconoCamion }).addTo(map).bindPopup(`<b>${v.nombre}</b>`);
                            } else {
                                marcadoresVehiculos[id].setLatLng(ultimaPos);
                            }
                            elementosZoom.push(marcadoresVehiculos[id]);

                            if (!polylinesVehiculos[id]) {
                                polylinesVehiculos[id] = L.polyline(v.historial, { color: '#28a745', weight: 6, opacity: 0.8 }).addTo(map);
                            } else {
                                polylinesVehiculos[id].setLatLngs(v.historial);
                            }

                            if (posicionUsuarioCoords) {
                                const dist = calcularDistanciaMetros(posicionUsuarioCoords, ultimaPos);
                                if (dist < menorDist) menorDist = dist;
                            }
                        }
                    }

                    document.getElementById('lbl-coor').textContent = `${activosCount} camión(es) activo(s)`;
                    if (posicionUsuarioCoords && menorDist < 9999999) {
                        let txt = menorDist > 1000 ? (menorDist/1000).toFixed(1) + " km" : menorDist + " m";
                        document.getElementById('lbl-distancia-usuario').innerHTML = `${txt} (~${Math.max(1, Math.round(menorDist/150))} min)`;
                    }

                    if (elementosZoom.length > 1) {
                        map.fitBounds(L.featureGroup(elementosZoom).getBounds().pad(0.3));
                    } else if (elementosZoom.length === 1 && marcadorUsuario) {
                        map.setView(posicionUsuarioCoords, 16);
                    }
                } catch (e) { console.error(e); }
            }

            function calcularDistanciaMetros(p1, p2) {
                const R = 6371e3;
                const dLat = (p2[0]-p1[0]) * Math.PI/180;
                const dLng = (p2[1]-p1[1]) * Math.PI/180;
                const a = Math.sin(dLat/2)**2 + Math.cos(p1[0]*Math.PI/180)*Math.cos(p2[0]*Math.PI/180)*Math.sin(dLng/2)**2;
                return Math.round(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)));
            }
        </script>
    </body>
    </html>
    """)

# 2. PANEL DEL CONDUCTOR - Se ve en "/conductor" (Inputs libres para cualquier camión y ruta)
@app.route('/conductor')
def panel_conductor():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ATA - Transmisor GPS</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; text-align: center; padding: 20px; background: #f0f2f5; margin: 0; }
            .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }
            input, select, button { width: 100%; padding: 12px; margin-top: 12px; font-size: 15px; border-radius: 8px; border: 1px solid #ccc; box-sizing: border-box; }
            button { background: #28a745; color: white; border: none; font-weight: bold; cursor: pointer; }
            button.detener { background: #dc3545; }
            #estado { margin-top: 15px; font-weight: bold; color: #333; font-size: 13px; line-height: 1.4; }
            label { text-align: left; display: block; font-size: 12px; font-weight: bold; color: #555; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🚛 Transmisor GPS Camión</h2>
            
            <label>Asigna la Ruta:</label>
            <select id="select-ruta">
                <option value="ruta_centro">Ruta Centro</option>
                <option value="ruta_norte">Ruta Norte</option>
                <option value="ruta_sur">Ruta Sur</option>
            </select>

            <label>Nombre o Número del Vehículo:</label>
            <input type="text" id="input-nombre-vehiculo" value="Camión #12" placeholder="Ej: Compactador 04">

            <button id="btn-transmitir" onclick="toggleTransmision()">🟢 Iniciar Transmisión GPS</button>
            <div id="estado">Estado: Detenido</div>
        </div>

        <script>
            let watchId = null;
            let transmitiendo = false;
            let esPrimerPunto = true;

            function toggleTransmision() {
                const btn = document.getElementById('btn-transmitir');
                const estadoDiv = document.getElementById('estado');
                const rutaSelect = document.getElementById('select-ruta');
                const nombreInput = document.getElementById('input-nombre-vehiculo');

                if (!transmitiendo) {
                    if (!navigator.geolocation) return alert("Sin soporte de GPS.");
                    if (!nombreInput.value.trim()) return alert("Por favor ingresa el nombre del camión.");

                    transmitiendo = true;
                    esPrimerPunto = true;
                    rutaSelect.disabled = true;
                    nombreInput.disabled = true;
                    btn.textContent = "🔴 Detener Transmisión";
                    btn.className = "detener";
                    estadoDiv.textContent = "Obteniendo señal GPS...";

                    watchId = navigator.geolocation.watchPosition(
                        async (position) => {
                            const lat = position.coords.latitude;
                            const lng = position.coords.longitude;
                            // Generamos un ID interno único basado en el texto del input sin espacios
                            const vehiculoId = nombreInput.value.trim().toLowerCase().replace(/\\s+/g, '_');
                            const rutaAsignada = rutaSelect.value;

                            estadoDiv.innerHTML = `Transmitiendo en vivo 🟢<br>Zona: ${rutaAsignada}<br>Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`;

                            try {
                                await fetch('/api/actualizar-gps', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ 
                                        vehiculo_id: vehiculoId, 
                                        nombre: nombreInput.value.trim(),
                                        ruta: rutaAsignada,
                                        lat: lat, 
                                        lng: lng,
                                        reiniciarHistorial: esPrimerPunto 
                                    })
                                });
                                esPrimerPunto = false;
                            } catch (e) { console.error("Error al enviar GPS", e); }
                        },
                        (error) => { estadoDiv.textContent = "Error GPS: " + error.message; },
                        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
                    );
                } else {
                    if (watchId !== null) navigator.geolocation.clearWatch(watchId);
                    transmitiendo = false;
                    rutaSelect.disabled = false;
                    nombreInput.disabled = false;
                    btn.textContent = "🟢 Iniciar Transmisión GPS";
                    btn.className = "";
                    estadoDiv.textContent = "Transmisión detenida.";
                }
            }
        </script>
    </body>
    </html>
    """)

# 3. API DINÁMICA: Registra o actualiza cualquier camión al vuelo
@app.route('/api/actualizar-gps', methods=['POST'])
def actualizar_gps():
    data = request.json
    vehiculo_id = data.get('vehiculo_id')
    nombre = data.get('nombre', vehiculo_id)
    ruta = data.get('ruta', 'ruta_general')
    lat = data.get('lat')
    lng = data.get('lng')
    reiniciar = data.get('reiniciarHistorial', False)

    # Si el camión es nuevo, Python lo crea automáticamente en el diccionario sin modificar código
    if vehiculo_id not in vehiculos_estado:
        vehiculos_estado[vehiculo_id] = {
            "ruta": ruta,
            "nombre": nombre,
            "historial": [],
            "activo": True
        }

    # Actualizamos sus datos actuales
    vehiculos_estado[vehiculo_id]['ruta'] = ruta
    vehiculos_estado[vehiculo_id]['nombre'] = nombre
    vehiculos_estado[vehiculo_id]['activo'] = True

    historial = vehiculos_estado[vehiculo_id]['historial']
    if reiniciar or not historial:
        vehiculos_estado[vehiculo_id]['historial'] = [[lat, lng]]
    else:
        if historial[-1] != [lat, lng]:
            historial.append([lat, lng])
        
    return jsonify({"status": "success"})

# 4. API PARA CONSULTAR TODOS LOS VEHÍCULOS ACTIVOS
@app.route('/api/obtener-vehiculos', methods=['GET'])
def obtener_vehiculos():
    return jsonify(vehiculos_estado)

if __name__ == '__main__':
    print("🚀 Servidor dinámico corriendo en http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)