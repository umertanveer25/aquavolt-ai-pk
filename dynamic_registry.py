
import os
import importlib.util
import concurrent.futures

PLUGIN_DIR = 'plugins/sensors'

def load_plugins():
    plugins = []
    if not os.path.exists(PLUGIN_DIR):
        return plugins
        
    for filename in os.listdir(PLUGIN_DIR):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]
            file_path = os.path.join(PLUGIN_DIR, filename)
            
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'fetch') and hasattr(module, 'SENSOR_INFO'):
                plugins.append(module)
                print(f'[REGISTRY] Auto-Discovered new satellite plugin: {module.SENSOR_INFO["name"]}')
    return plugins

def run_dynamic_ensemble():
    print('Scanning plugins/sensors/ for external satellites...')
    plugins = load_plugins()
    if not plugins:
        print('No plugins found.')
        return
        
    results = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(p.fetch): p.SENSOR_INFO['name'] for p in plugins}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                print(f'Sensor {name} failed: {e}')
                
    print('\n[ENSEMBLE FUSION DATA LAKE INGESTION]')
    for name, data in results.items():
        print(f' -> Ingested data from {name}: {data}')
        
if __name__ == '__main__':
    run_dynamic_ensemble()
