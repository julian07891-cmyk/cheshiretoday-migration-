import React, { useState, useEffect } from 'react';
import { Cloud, Sun, CloudRain, CloudSnow, Wind, Droplets, Thermometer, ExternalLink, ChevronRight } from 'lucide-react';

const WeatherWidget = ({ compact = false }) => {
  const [weather, setWeather] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForecast, setShowForecast] = useState(false);

  useEffect(() => {
    fetchWeather();
    // Refresh weather every 30 minutes
    const interval = setInterval(fetchWeather, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchWeather = async () => {
    try {
      // Using Open-Meteo API (free, no API key required)
      // Chester, Cheshire coordinates: 53.19, -2.89
      const response = await fetch(
        'https://api.open-meteo.com/v1/forecast?latitude=53.19&longitude=-2.89&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=Europe/London&forecast_days=5'
      );
      
      if (!response.ok) throw new Error('Weather fetch failed');
      
      const data = await response.json();
      setWeather({
        temp: Math.round(data.current.temperature_2m),
        humidity: data.current.relative_humidity_2m,
        windSpeed: Math.round(data.current.wind_speed_10m),
        weatherCode: data.current.weather_code,
        high: Math.round(data.daily.temperature_2m_max[0]),
        low: Math.round(data.daily.temperature_2m_min[0])
      });
      
      // Set 5-day forecast
      const forecastData = data.daily.time.map((date, idx) => ({
        date: new Date(date),
        high: Math.round(data.daily.temperature_2m_max[idx]),
        low: Math.round(data.daily.temperature_2m_min[idx]),
        weatherCode: data.daily.weather_code[idx]
      }));
      setForecast(forecastData);
      
      setLoading(false);
    } catch (err) {
      console.error('Weather error:', err);
      setError('Unable to load weather');
      setLoading(false);
    }
  };

  // Weather code to icon and description mapping (WMO codes)
  const getWeatherInfo = (code) => {
    if (code <= 3) return { icon: Sun, desc: 'Clear', color: 'text-yellow-500' };
    if (code <= 48) return { icon: Cloud, desc: 'Cloudy', color: 'text-gray-500' };
    if (code <= 67) return { icon: CloudRain, desc: 'Rainy', color: 'text-blue-500' };
    if (code <= 77) return { icon: CloudSnow, desc: 'Snowy', color: 'text-blue-300' };
    if (code <= 82) return { icon: CloudRain, desc: 'Showers', color: 'text-blue-600' };
    return { icon: Cloud, desc: 'Cloudy', color: 'text-gray-500' };
  };

  const formatDay = (date) => {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';
    return date.toLocaleDateString('en-GB', { weekday: 'short' });
  };

  const openBBCWeather = () => {
    window.open('https://www.bbc.co.uk/weather/2653228', '_blank'); // Chester weather page
  };

  if (loading) {
    return (
      <div className={`${compact ? 'p-2' : 'p-4'} bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-lg animate-pulse`}>
        <div className="h-8 bg-blue-200 dark:bg-blue-700 rounded w-20"></div>
      </div>
    );
  }

  if (error || !weather) {
    return null; // Don't show widget if weather unavailable
  }

  const { icon: WeatherIcon, desc, color } = getWeatherInfo(weather.weatherCode);

  if (compact) {
    return (
      <button 
        onClick={openBBCWeather}
        className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/50 dark:to-blue-800/50 rounded-full hover:from-blue-100 hover:to-blue-200 dark:hover:from-blue-800/50 dark:hover:to-blue-700/50 transition-colors cursor-pointer"
        title="Click for full weather forecast"
      >
        <WeatherIcon className={`h-4 w-4 ${color}`} />
        <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">{weather.temp}°C</span>
        <span className="text-xs text-gray-500 dark:text-gray-400">Cheshire</span>
        <ExternalLink className="h-3 w-3 text-gray-400" />
      </button>
    );
  }

  return (
    <div className="bg-gradient-to-br from-blue-50 via-blue-100 to-sky-100 dark:from-blue-900/40 dark:via-blue-800/40 dark:to-sky-900/40 rounded-lg shadow-sm overflow-hidden">
      {/* Current Weather - Clickable */}
      <div 
        className="p-4 cursor-pointer hover:bg-blue-100/50 dark:hover:bg-blue-800/30 transition-colors"
        onClick={() => setShowForecast(!showForecast)}
      >
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200">Cheshire Weather</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">Chester</p>
          </div>
          <div className="flex items-center gap-2">
            <WeatherIcon className={`h-10 w-10 ${color}`} />
            <ChevronRight className={`h-4 w-4 text-gray-400 transition-transform ${showForecast ? 'rotate-90' : ''}`} />
          </div>
        </div>
        
        <div className="flex items-end gap-2 mb-3">
          <span className="text-4xl font-bold text-gray-900 dark:text-white">{weather.temp}°</span>
          <span className="text-lg text-gray-600 dark:text-gray-300 mb-1">{desc}</span>
        </div>
        
        <div className="flex items-center gap-4 text-xs text-gray-600 dark:text-gray-400">
          <div className="flex items-center gap-1">
            <Thermometer className="h-3 w-3" />
            <span>H: {weather.high}° L: {weather.low}°</span>
          </div>
          <div className="flex items-center gap-1">
            <Wind className="h-3 w-3" />
            <span>{weather.windSpeed} km/h</span>
          </div>
          <div className="flex items-center gap-1">
            <Droplets className="h-3 w-3" />
            <span>{weather.humidity}%</span>
          </div>
        </div>
      </div>

      {/* 5-Day Forecast - Expandable */}
      {showForecast && forecast.length > 0 && (
        <div className="border-t border-blue-200 dark:border-blue-700 bg-white/50 dark:bg-gray-800/50 p-4">
          <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-300 mb-3 uppercase tracking-wide">
            5-Day Forecast
          </h4>
          <div className="space-y-2">
            {forecast.map((day, idx) => {
              const { icon: DayIcon, color: dayColor } = getWeatherInfo(day.weatherCode);
              return (
                <div 
                  key={idx} 
                  className="flex items-center justify-between py-2 border-b border-blue-100 dark:border-blue-800 last:border-0"
                >
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300 w-20">
                    {formatDay(day.date)}
                  </span>
                  <DayIcon className={`h-5 w-5 ${dayColor}`} />
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-semibold text-gray-900 dark:text-white">{day.high}°</span>
                    <span className="text-gray-400">/</span>
                    <span className="text-gray-500 dark:text-gray-400">{day.low}°</span>
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Link to full forecast */}
          <button
            onClick={openBBCWeather}
            className="w-full mt-4 flex items-center justify-center gap-2 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors text-sm font-medium"
          >
            <span>Full BBC Weather Forecast</span>
            <ExternalLink className="h-4 w-4" />
          </button>
        </div>
      )}
      
      {/* Quick link when collapsed */}
      {!showForecast && (
        <div className="px-4 pb-3">
          <button
            onClick={openBBCWeather}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
          >
            <span>View full forecast</span>
            <ExternalLink className="h-3 w-3" />
          </button>
        </div>
      )}
    </div>
  );
};

export default WeatherWidget;
