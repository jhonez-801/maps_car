from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

vehiculos_estado = {}

@app.route('/')
def cliente_mapa():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Ruta Basura en Vivo - ATA Ingeniería</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
        <style>
            * { box-sizing: border-box; }
            html, body { 
                margin: 0; padding: 0; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                width: 100%; height: 100%; overflow: hidden; background: #f8f9fa; 
            }
            body { display: flex; flex-direction: row; position: relative; }
            
            #sidebar { 
                width: 380px; height: 100%; background: #ffffff; 
                box-shadow: 2px 0 10px rgba(0,0,0,0.15); z-index: 1000; 
                padding: 15px; display: flex; flex-direction: column; 
                overflow-y: auto; -webkit-overflow-scrolling: touch;
                transition: transform 0.3s ease-in-out;
            }
            
            #sidebar-content { flex: 1 0 auto; padding-bottom: 20px; }
            #map { flex: 1; height: 100%; }
            
            h2 { font-size: 16px; color: #2c3e50; margin-top: 0; margin-bottom: 6px; }
            .instructions { font-size: 12px; color: #555; margin-bottom: 12px; line-height: 1.4; }
            .instructions b { color: #28a745; }
            
            .route-btn { 
                display: block; width: 100%; padding: 12px; margin-bottom: 8px; 
                background: #ffffff; border: 2px solid #e9ecef; border-radius: 8px; 
                text-align: left; cursor: pointer; font-size: 13px; font-weight: 600; color: #333; 
            }
            .route-btn.active { background: #c8e6c9; border-color: #2e7d32; color: #1b5e20; }
            .route-btn span { display: block; font-size: 11px; color: #666; font-weight: normal; margin-top: 3px; }

            .btn-gps-usuario { 
                background: #007bff; color: white; border: none; width: 100%; 
                padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; 
                margin-bottom: 12px; font-size: 13px; box-shadow: 0 2px 4px rgba(0,0,0,0.15); 
            }

            .menu-toggle-btn {
                background: #343a40; color: white; border: none; width: 100%; 
                padding: 10px; border-radius: 8px; font-weight: bold; cursor: pointer; 
                margin-bottom: 15px; font-size: 13px; display: flex; align-items: center; 
                justify-content: center; gap: 8px;
            }

            .driver-link-container {
                background: #e2e3e5; border-radius: 8px; padding: 12px; 
                margin-bottom: 15px; text-align: center;
            }
            .driver-btn {
                display: inline-block; background: #28a745; color: white; border: none; 
                padding: 8px 15px; border-radius: 6px; font-weight: bold; font-size: 12px; 
                margin-top: 5px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            #modal-conductor {
                display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0, 0, 0, 0.6); z-index: 2000; justify-content: center; align-items: center;
            }
            .modal-content {
                background: white; padding: 25px; border-radius: 10px; width: 320px; 
                text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }
            .modal-content h3 { margin-top: 0; color: #2c3e50; font-size: 18px; }
            .modal-content input {
                width: 100%; padding: 10px; margin: 12px 0; border: 1px solid #ccc; 
                border-radius: 6px; font-size: 14px; text-align: center;
            }
            .modal-actions { display: flex; gap: 10px; margin-top: 10px; }
            .modal-actions button { flex: 1; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
            .btn-confirmar { background: #28a745; color: white; }
            .btn-cancelar { background: #6c757d; color: white; }

            .status-card { 
                margin-top: 10px; margin-bottom: 10px; padding: 12px; background: #e8f4ff; 
                border-radius: 8px; font-size: 12px; color: #004085; line-height: 1.5; border-left: 4px solid #007bff; 
            }
            
            .footer-ata { 
                text-align: center; font-size: 11px; color: #555; padding: 15px 0 10px 0; 
                margin-top: 15px; border-top: 1px solid #cbd3da; background: #ffffff;
            }

            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
            .live-indicator { display: inline-block; width: 8px; height: 8px; background: #28a745; border-radius: 50%; margin-right: 5px; animation: pulse 1.5s infinite; }

            /* Botón flotante superior para abrir el menú en celulares */
            .floating-menu-btn {
                position: absolute; top: 15px; left: 15px; z-index: 1100; background: white; 
                border: 2px solid #ced4da; width: 45px; height: 45px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); 
                font-size: 20px; cursor: pointer; display: none; align-items: center; justify-content: center;
            }

            /* ADAPTACIÓN MÓVIL OPTIMIZADA: El mapa ocupa el 100% de la pantalla y el panel es un cajón inferior */
            @media (max-width: 768px) {
                body { flex-direction: column; }
                #map { width: 100%; height: 100vh; position: absolute; top: 0; left: 0; z-index: 1; }
                #sidebar { 
                    position: absolute; bottom: 0; left: 0; width: 100%; height: 65vh; 
                    flex: none; box-shadow: 0 -4px 15px rgba(0,0,0,0.3);
                    border-top-left-radius: 16px; border-top-right-radius: 16px;
                    z-index: 1200;
                    transform: translateY(0); /* Por defecto abierto para que el vecino elija ruta al entrar, o translateY(calc(100% - 60px)) si prefieres que se oculte más */
                    transition: transform 0.3s ease-in-out;
                }
                #sidebar.collapsed { 
                    transform: translateY(calc(100% - 65px)); /* Deja una pestaña visible abajo para reabrirlo */
                }
                .floating-menu-btn { display: flex; }
            }
        </style>
    </head>
    <body>

        <!-- Botón flotante para mostrar el menú si está oculto en móvil -->
        <button class="floating-menu-btn" onclick="toggleSidebarMovil()" id="btn-toggle-movil" style="font-size: 18px; width: auto; padding: 0 12px; gap: 6px;">☰ Rutas</button>

        <div id="modal-conductor">
            <div class="modal-content">
                <h3>🔐 Acceso Conductor</h3>
                <p style="font-size: 12px; color: #666;">Ingresa tu clave de registro:</p>
                <input type="password" id="input-clave-conductor" placeholder="Clave de acceso">
                <div class="modal-actions">
                    <button class="btn-cancelar" onclick="cerrarModalConductor()">Cancelar</button>
                    <button class="btn-confirmar" onclick="validarClaveConductor()">Ingresar</button>
                </div>
            </div>
        </div>

        <div id="sidebar" class="">
            <div id="sidebar-content">
                <div class="driver-link-container">
                    <span style="font-size: 12px; color: #333; display: block; font-weight: bold;">¿Eres conductor de ruta?</span>
                    <button class="driver-btn" onclick="abrirModalConductor()">🧑‍✈️ Ingresar como Conductor</button>
                </div>

                <h2>🚚 Rutas Activas en Vivo</h2>
                <p class="instructions">
                    <b>Selecciona una ruta activa</b> para hacer zoom y ver sus unidades en tiempo real.
                </p>

                <button class="btn-gps-usuario" onclick="ubicarCliente()">📍 Ubicar mi posición / Casa</button>

                <div id="contenedor-rutas">
                    <p style="font-size: 12px; color: #666; text-align: center;">Cargando rutas activas...</p>
                </div>

                <div id="panel-estado" class="status-card" style="display:none;">
                    <b><span class="live-indicator"></span>Monitoreando:</b> <span id="lbl-ruta-actual">Ninguna</span><br>
                    🚛 <b>Unidades:</b> <span id="lbl-coor">Conectando...</span><br>
                    📏 <b>Distancia / Tiempo:</b> <span id="lbl-distancia-usuario" style="color: #d9534f; font-weight: bold;">Pulsa "Ubicar mi posición"</span>
                </div>
            </div>

            <button class="menu-toggle-btn" onclick="toggleSidebarMovil()">🔽 Ocultar Panel (Ver Mapa Grande)</button>

            <div class="footer-ata">
                © 2026 <b>ATA</b> (Aplicaciones Tecnológicas Avanzadas). Todos los derechos reservados.
            </div>
        </div>

        <div id="map"></div>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
        <script>
            const map = L.map('map', { zoomControl: false }).setView([5.3377, -72.3961], 15);
            L.control.zoom({ position: 'topright' }).addTo(map);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '© OpenStreetMap - ATA Ingeniería'
            }).addTo(map);

            let rutaActivaId = null;
            let marcadorUsuario = null;
            let posicionUsuarioCoords = null;
            let centradoInicialRealizado = false;

            let marcadoresVehiculos = {}; 
            let polylinesVehiculos = {};

            const iconoCamion = L.divIcon({
                className: 'custom-camion-icon',
                html: '<div style="background:#28a745; color:white; padding:6px 8px; border-radius:50%; font-size:16px; box-shadow:0 3px 10px rgba(0,0,0,0.4); text-align:center; width:24px; height:24px; display:flex; align-items:center; justify-content:center;">🚛</div>',
                iconSize: [36, 36], iconAnchor: [18, 18]
            });

            const iconoUsuario = L.divIcon({
                className: 'custom-user-icon',
                html: '<div style="background:#007bff; color:white; padding:6px 8px; border-radius:50%; font-size:16px; box-shadow:0 3px 10px rgba(0,0,0,0.4); text-align:center; width:24px; height:24px; display:flex; align-items:center; justify-content:center;">🏠</div>',
                iconSize: [36, 36], iconAnchor: [18, 18]
            });

            function abrirModalConductor() {
                document.getElementById('modal-conductor').style.display = 'flex';
                document.getElementById('input-clave-conductor').value = '';
                document.getElementById('input-clave-conductor').focus();
            }

            function cerrarModalConductor() {
                document.getElementById('modal-conductor').style.display = 'none';
            }

            function validarClaveConductor() {
                const claveIngresada = document.getElementById('input-clave-conductor').value;
                if (claveIngresada === "ata2026") {
                    cerrarModalConductor();
                    window.open("/conductor", "_blank");
                } else {
                    alert("❌ Clave incorrecta. Acceso denegado.");
                    document.getElementById('input-clave-conductor').value = '';
                    document.getElementById('input-clave-conductor').focus();
                }
            }

            // Control para contraer/expandir el panel inferior en celulares
            function toggleSidebarMovil() {
                const sidebar = document.getElementById('sidebar');
                sidebar.classList.toggle('collapsed');
                setTimeout(() => { map.invalidateSize(); }, 300);
            }

            map.on('dragstart movestart', () => { centradoInicialRealizado = true; });

            function ubicarCliente() {
                if (!navigator.geolocation) return alert("Tu navegador no soporta geolocalización.");
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        posicionUsuarioCoords = [position.coords.latitude, position.coords.longitude];
                        if (!marcadorUsuario) {
                            marcadorUsuario = L.marker(posicionUsuarioCoords, { icon: iconoUsuario }).addTo(map)
                                .bindPopup("<b>Tu Ubicación / Casa</b>").openPopup();
                        } else {
                            marcadorUsuario.setLatLng(posicionUsuarioCoords);
                        }
                        map.setView(posicionUsuarioCoords, 16);
                        consultarPosicionRuta();
                        if (window.innerWidth <= 768) {
                            document.getElementById('sidebar').classList.add('collapsed');
                            setTimeout(() => { map.invalidateSize(); }, 300);
                        }
                    },
                    () => alert("No se pudo obtener tu ubicación. Revisa los permisos de GPS."),
                    { enableHighAccuracy: true, timeout: 10000 }
                );
            }

            function seleccionarRuta(idRuta, nombreRuta, event) {
                document.querySelectorAll('.route-btn').forEach(btn => btn.classList.remove('active'));
                if (event && event.currentTarget) event.currentTarget.classList.add('active');

                document.getElementById('panel-estado').style.display = 'block';
                document.getElementById('lbl-ruta-actual').textContent = nombreRuta;

                rutaActivaId = idRuta;
                centradoInicialRealizado = false;
                consultarPosicionRuta();

                if (window.innerWidth <= 768) {
                    document.getElementById('sidebar').classList.add('collapsed');
                    setTimeout(() => { map.invalidateSize(); }, 300);
                }
            }

            async function consultarPosicionRuta() {
                try {
                    const res = await fetch('/api/obtener-vehiculos');
                    const vehiculosMap = await res.json();

                    let rutasActivasMap = {};
                    for (let vId in vehiculosMap) {
                        let v = vehiculosMap[vId];
                        let vRuta = v.ruta;
                        let historial = v.historial;

                        if (vRuta && historial && historial.length > 0) {
                            if (!rutasActivasMap[vRuta]) {
                                rutasActivasMap[vRuta] = { nombre: vRuta.replace('_', ' ').toUpperCase(), cantidad: 0 };
                            }
                            rutasActivasMap[vRuta].cantidad++;
                        }
                    }

                    const contenedorRutas = document.getElementById('contenedor-rutas');
                    contenedorRutas.innerHTML = '';

                    if (Object.keys(rutasActivasMap).length === 0) {
                        contenedorRutas.innerHTML = '<p style="font-size: 12px; color: #d9534f; text-align: center;">No hay rutas activas en este momento.</p>';
                    } else {
                        for (let rId in rutasActivasMap) {
                            let info = rutasActivasMap[rId];
                            let btn = document.createElement('button');
                            btn.className = `route-btn ${rutaActivaId === rId ? 'active' : ''}`;
                            btn.innerHTML = `🚛 ${info.nombre}<span>${info.cantidad} unidad(es) activa(s)</span>`;
                            btn.onclick = (e) => seleccionarRuta(rId, info.nombre, e);
                            contenedorRutas.appendChild(btn);
                        }
                    }

                    if (!rutaActivaId) return;

                    let elementosZoom = [];
                    if (marcadorUsuario) elementosZoom.push(marcadorUsuario);

                    let activosCount = 0;
                    let menorDistanciaMetros = 9999999;
                    let idsVehiculosEnEstaRuta = new Set();

                    for (let vId in vehiculosMap) {
                        let v = vehiculosMap[vId];
                        let vRuta = v.ruta;
                        let vNombre = v.nombre || ('Camión ' + vId);
                        let historial = v.historial;

                        if (vRuta === rutaActivaId && historial && historial.length > 0) {
                            idsVehiculosEnEstaRuta.add(vId);
                            activosCount++;
                            let ultimaPos = historial[historial.length - 1];

                            if (!marcadoresVehiculos[vId]) {
                                marcadoresVehiculos[vId] = L.marker(ultimaPos, { icon: iconoCamion }).addTo(map)
                                    .bindPopup(`<b>${vNombre}</b><br>Unidad en servicio`);
                            } else {
                                marcadoresVehiculos[vId].setLatLng(ultimaPos);
                            }
                            elementosZoom.push(marcadoresVehiculos[vId]);

                            if (!polylinesVehiculos[vId]) {
                                polylinesVehiculos[vId] = L.polyline(historial, {
                                    color: '#007bff', weight: 6, opacity: 0.8, lineCap: 'round', lineJoin: 'round'
                                }).addTo(map);
                            } else {
                                polylinesVehiculos[vId].setLatLngs(historial);
                            }

                            if (posicionUsuarioCoords) {
                                const dist = calcularDistanciaMetros(posicionUsuarioCoords, ultimaPos);
                                if (dist < menorDistanciaMetros) menorDistanciaMetros = dist;
                            }
                        }
                    }

                    for (let vId in marcadoresVehiculos) {
                        if (!idsVehiculosEnEstaRuta.has(vId)) {
                            map.removeLayer(marcadoresVehiculos[vId]);
                            delete marcadoresVehiculos[vId];
                            if (polylinesVehiculos[vId]) {
                                map.removeLayer(polylinesVehiculos[vId]);
                                delete polylinesVehiculos[vId];
                            }
                        }
                    }

                    if (activosCount > 0) {
                        document.getElementById('lbl-coor').textContent = `${activosCount} unidad(es) en vivo`;
                        if (posicionUsuarioCoords && menorDistanciaMetros < 9999999) {
                            let txtDist = menorDistanciaMetros > 1000 ? (menorDistanciaMetros/1000).toFixed(1) + " km" : menorDistanciaMetros + " m";
                            let minutosAprox = Math.max(1, Math.round(menorDistanciaMetros / 130));
                            document.getElementById('lbl-distancia-usuario').innerHTML = `${txtDist} (Llega en ~<b>${minutosAprox} min</b>)`;
                        }
                    } else {
                        document.getElementById('lbl-coor').textContent = 'Sin unidades activas en esta ruta';
                        document.getElementById('lbl-distancia-usuario').innerHTML = 'Ruta inactiva';
                    }

                    if (!centradoInicialRealizado && elementosZoom.length > 0) {
                        const grupo = L.featureGroup(elementosZoom);
                        map.fitBounds(grupo.getBounds().pad(0.3));
                        centradoInicialRealizado = true; 
                    }

                } catch (e) {
                    console.error("Error al consultar la API de vehículos:", e);
                }
            }

            function calcularDistanciaMetros(p1, p2) {
                const R = 6371e3;
                const dLat = (p2[0]-p1[0]) * Math.PI/180;
                const dLng = (p2[1]-p1[1]) * Math.PI/180;
                const a = Math.sin(dLat/2)**2 + Math.cos(p1[0]*Math.PI/180)*Math.cos(p2[0]*Math.PI/180)*Math.sin(dLng/2)**2;
                return Math.round(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)));
            }

            setInterval(consultarPosicionRuta, 3000);
            consultarPosicionRuta();
        </script>
    </body>
    </html>
    """)

@app.route('/conductor')
def panel_conductor():
    return "Página del Conductor"

@app.route('/api/actualizar-gps', methods=['POST'])
def actualizar_gps():
    data = request.json
    vehiculo_id = data.get('vehiculo_id')
    nombre = data.get('nombre', vehiculo_id)
    ruta = data.get('ruta', 'ruta_general')
    lat = data.get('lat')
    lng = data.get('lng')
    reiniciar = data.get('reiniciarHistorial', False)

    if vehiculo_id not in vehiculos_estado:
        vehiculos_estado[vehiculo_id] = {
            "ruta": ruta, "nombre": nombre, "historial": [], "activo": True
        }

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

@app.route('/api/obtener-vehiculos', methods=['GET'])
def obtener_vehiculos():
    return jsonify(vehiculos_estado)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
