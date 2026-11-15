document.addEventListener('DOMContentLoaded', function(){

    const apiKey = 'cb1_53r4_1_ccad070d4d17944ed71283fa';

    //leaflet setup
    const map = L.map('map').setView([0, 0], 2);
    const tileLayer = L.tileLayer(`https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png?key=${apiKey}`, {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    }).addTo(map);



})