from flask import Blueprint, jsonify, request, render_template
from app.controllers.device_controller import DeviceController
from app.controllers.consumption_controller import ConsumptionController
from app.controllers.prediction_controller import PredictionController
from datetime import datetime, timedelta
from app.utils.data_collector import DataCollector

api_bp = Blueprint('api', __name__)

# Root endpoint for API documentation
@api_bp.route('/', methods=['GET'])
def api_docs():
    return render_template('index.html')

# Device endpoints
@api_bp.route('/devices', methods=['GET'])
def get_devices():
    devices = DeviceController.get_all_devices()
    return jsonify(devices)

@api_bp.route('/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    device = DeviceController.get_device_by_id(device_id)
    if device:
        return jsonify(device)
    return jsonify({'error': 'Device not found'}), 404

@api_bp.route('/devices', methods=['POST'])
def create_device():
    data = request.json
    if not data or 'name' not in data or 'rated_power' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    meter_number = data.get('meter_number', '')
    relay_status = data.get('relay_status', 'OFF')
    
    device = DeviceController.create_device(
        data['name'], 
        meter_number, 
        data['rated_power'], 
        relay_status
    )
    return jsonify(device), 201

@api_bp.route('/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    device = DeviceController.update_device(
        device_id, 
        name=data.get('name'), 
        meter_number=data.get('meter_number'),
        rated_power=data.get('rated_power'),
        relay_status=data.get('relay_status')
    )
    
    if device:
        return jsonify(device)
    return jsonify({'error': 'Device not found'}), 404

@api_bp.route('/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    success = DeviceController.delete_device(device_id)
    if success:
        return jsonify({'message': 'Device deleted successfully'})
    return jsonify({'error': 'Device not found'}), 404

@api_bp.route('/devices/sync', methods=['POST'])
def sync_devices():
    data = request.get_json(silent=True) or {}
    api_url = data.get('api_url', DataCollector.DEVICES_API_URL)
    
    success = DeviceController.sync_devices_from_api(api_url)
    if success:
        return jsonify({'message': 'Devices synced successfully'})
    return jsonify({'error': 'Failed to sync devices'}), 500

# Consumption endpoints
@api_bp.route('/consumption/<int:device_id>', methods=['GET'])
def get_device_consumption(device_id):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if end_date:
        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    records = ConsumptionController.get_device_consumption(device_id, start_date, end_date)
    return jsonify(records)

@api_bp.route('/consumption/total', methods=['GET'])
def get_total_consumption():
    device_ids = request.args.get('device_ids')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if device_ids:
        device_ids = [int(id) for id in device_ids.split(',')]
    if start_date:
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if end_date:
        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    totals = ConsumptionController.get_total_consumption(device_ids, start_date, end_date)
    return jsonify(totals)

@api_bp.route('/consumption', methods=['POST'])
def add_consumption_record():
    data = request.json
    if not data or 'device_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    record = ConsumptionController.add_consumption_record(
        device_id=data['device_id'],
        voltage=data['voltage'],
        current=data['current'],
        time_on=data['time_on'],
        active_energy=data['active_energy'],
        reading_timestamp=datetime.fromisoformat(data['reading_timestamp'].replace('Z', '+00:00'))
    )
    
    return jsonify(record), 201

@api_bp.route('/consumption/sync/<int:device_id>', methods=['POST'])
def sync_consumption(device_id):
    data = request.get_json(silent=True) or {}
    api_url = data.get('api_url', f"{DataCollector.CONSUMPTION_API_BASE_URL}/{device_id}")
    
    success = ConsumptionController.sync_consumption_from_api(api_url, device_id)
    if success:
        return jsonify({'message': 'Consumption data synced successfully'})
    return jsonify({'error': 'Failed to sync consumption data'}), 500

# Prediction endpoints
@api_bp.route('/predictions/energy', methods=['GET'])
def get_energy_predictions():
    device_id = request.args.get('device_id')
    prediction_date = request.args.get('date')
    
    if device_id:
        device_id = int(device_id)
    if prediction_date:
        prediction_date = datetime.strptime(prediction_date, '%Y-%m-%d').date()
    
    predictions = PredictionController.get_energy_predictions(device_id, prediction_date)
    return jsonify(predictions)

@api_bp.route('/predictions/peak', methods=['GET'])
def get_peak_predictions():
    prediction_date = request.args.get('date')
    
    if prediction_date:
        prediction_date = datetime.strptime(prediction_date, '%Y-%m-%d').date()
    
    predictions = PredictionController.get_peak_demand_predictions(prediction_date)
    return jsonify(predictions)

@api_bp.route('/predictions/train', methods=['POST'])
def train_models():
    # Get JSON data if provided, otherwise use empty dict
    data = request.get_json(silent=True) or {}
    device_id = data.get('device_id')
    
    if device_id:
        # Train model for specific device
        success = PredictionController.train_energy_prediction_model(device_id)
        if success:
            return jsonify({'message': f'Energy prediction model for device {device_id} trained successfully'})
        return jsonify({'error': 'Failed to train model, not enough data'}), 400
    else:
        # Train peak demand model
        success_peak = PredictionController.train_peak_demand_model()
        if success_peak:
            return jsonify({'message': 'Peak demand prediction model trained successfully'})
        return jsonify({'error': 'Failed to train model, not enough data'}), 400

@api_bp.route('/predictions/generate', methods=['POST'])
def generate_predictions():
    data = request.get_json(silent=True) or {}
    days_ahead = data.get('days_ahead', 1)
    
    success = PredictionController.generate_predictions(days_ahead)
    if success:
        return jsonify({'message': f'Predictions generated for the next {days_ahead} days'})
    return jsonify({'error': 'Failed to generate predictions'}), 500

# Add these new endpoints to the existing api_bp Blueprint

@api_bp.route('/predictions/all', methods=['GET'])
def get_all_predictions():
    """Get all predictions for a date range"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    device_ids = request.args.get('device_ids')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    if device_ids:
        device_ids = [int(id) for id in device_ids.split(',')]
    
    predictions = PredictionController.get_all_predictions(start_date, end_date, device_ids)
    return jsonify(predictions)

@api_bp.route('/predictions/device/<int:device_id>/summary', methods=['GET'])
def get_device_predictions_summary(device_id):
    """Get a summary of predictions for a specific device"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    summary = PredictionController.get_device_predictions_summary(device_id, start_date, end_date)
    if summary:
        return jsonify(summary)
    return jsonify({'error': 'Device not found'}), 404

@api_bp.route('/predictions/peak/summary', methods=['GET'])
def get_peak_demand_summary():
    """Get a summary of peak demand predictions"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    summary = PredictionController.get_peak_demand_summary(start_date, end_date)
    return jsonify(summary)

@api_bp.route('/dashboard/overview', methods=['GET'])
def get_dashboard_overview():
    """Get an overview of energy consumption and predictions for the dashboard"""
    # Get today's date
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Get all devices
    devices = DeviceController.get_all_devices()
    
    # Get today's energy predictions
    energy_predictions = PredictionController.get_all_predictions(today, today)
    
    # Get peak demand for today
    peak_demand = PredictionController.get_peak_demand_summary(today, today)
    
    # Calculate total predicted energy for today and tomorrow
    today_total = 0
    tomorrow_total = 0
    
    today_str = today.isoformat()
    tomorrow_str = tomorrow.isoformat()
    
    if today_str in energy_predictions.get('daily_summaries', {}):
        for device_id, energy in energy_predictions['daily_summaries'][today_str]['total_energy'].items():
            today_total += energy
    
    # Get tomorrow's predictions
    tomorrow_predictions = PredictionController.get_all_predictions(tomorrow, tomorrow)
    
    if tomorrow_str in tomorrow_predictions.get('daily_summaries', {}):
        for device_id, energy in tomorrow_predictions['daily_summaries'][tomorrow_str]['total_energy'].items():
            tomorrow_total += energy
    
    # Format response
    result = {
        'date': today.isoformat(),
        'devices_count': len(devices),
        'today_predicted_energy': today_total,
        'tomorrow_predicted_energy': tomorrow_total,
        'energy_change_percentage': ((tomorrow_total - today_total) / max(today_total, 1)) * 100 if today_total > 0 else 0,
        'peak_demand': peak_demand['overall_peak']['demand'] if peak_demand['overall_peak']['demand'] > 0 else 0,
        'peak_hour': peak_demand['overall_peak']['hour'] if peak_demand['overall_peak']['hour'] is not None else 0,
        'devices': devices,
        'hourly_predictions': {}
    }
    
    # Add hourly predictions for today
    if today_str in energy_predictions.get('energy_predictions', {}):
        for device_id in energy_predictions['energy_predictions'][today_str]:
            for hour, data in energy_predictions['energy_predictions'][today_str][device_id].items():
                if hour not in result['hourly_predictions']:
                    result['hourly_predictions'][hour] = {}
                result['hourly_predictions'][hour][device_id] = data['predicted_energy']
    
    return jsonify(result)
