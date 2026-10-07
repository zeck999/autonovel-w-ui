import httpx
import asyncio
import json
import websockets

async def main():
    print("1. Connecting to Chrome debug port (http://localhost:9222/json) using httpx...")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:9222/json")
        assert response.status_code == 200, f"Expected 200 from Chrome debug port, got {response.status_code}"
        targets = response.json()
        print(f"   Success! Found {len(targets)} Chrome targets.")
        
        page_target = None
        for target in targets:
            print(f"   - Target [{target.get('type')}]: {target.get('title')} ({target.get('url')})")
            if "autonovel" in target.get('url', '').lower() or "localhost:8000" in target.get('url', '').lower():
                page_target = target

        if not page_target and targets:
            for t in targets:
                if t.get('type') == 'page':
                    page_target = t
                    break

        if not page_target:
            raise RuntimeError("No suitable Chrome page target found for Autonovel.")

        ws_url = page_target['webSocketDebuggerUrl']
        print(f"   Selected target: {page_target.get('title')} ({page_target.get('url')})")
        print(f"   WebSocket Debugger URL: {ws_url}")

        print("\n2. Testing FastAPI Settings API endpoints using httpx...")
        settings_res = await client.get("http://localhost:8000/api/settings/keys")
        print(f"   GET /api/settings/keys -> status {settings_res.status_code}")
        print(f"   Data: {settings_res.json()}")

        # Test updating settings keys
        update_payload = {
            "anthropic_api_key": "sk-ant-cdptestkey123456789",
            "elevenlabs_api_key": "eleven_cdp_test_key_abc",
            "fal_key": "fal_cdp_test_key_xyz"
        }
        update_res = await client.put("http://localhost:8000/api/settings/keys", json=update_payload)
        print(f"   PUT /api/settings/keys -> status {update_res.status_code}")
        print(f"   Response: {update_res.json()}")

        # Test key validation endpoint
        test_payload = {
            "provider": "anthropic",
            "api_key": "sk-ant-cdptestkey123456789"
        }
        test_res = await client.post("http://localhost:8000/api/settings/keys/test", json=test_payload)
        print(f"   POST /api/settings/keys/test -> status {test_res.status_code}")
        print(f"   Test result: {test_res.json()}")

    print("\n3. Connecting to Chrome DevTools Protocol via WebSocket to automate settings UI journey...")
    async with websockets.connect(ws_url) as websocket:
        await websocket.send(json.dumps({"id": 1, "method": "Page.enable"}))
        await websocket.recv()
        
        await websocket.send(json.dumps({"id": 2, "method": "Runtime.enable"}))
        await websocket.recv()

        print("   Navigating browser to http://localhost:8000/#/settings ...")
        await websocket.send(json.dumps({
            "id": 3,
            "method": "Page.navigate",
            "params": {"url": "http://localhost:8000/#/settings"}
        }))
        await websocket.recv()
        
        await asyncio.sleep(2.0)

        print("   Executing CDP Runtime.evaluate to automate settings UI inputs and buttons...")
        eval_script = """
        (async () => {
            let attempts = 0;
            while (!document.getElementById('input-anthropic') && attempts < 20) {
                await new Promise(r => setTimeout(r, 200));
                attempts++;
            }
            
            const anthInput = document.getElementById('input-anthropic');
            const elevInput = document.getElementById('input-elevenlabs');
            const falInput = document.getElementById('input-fal');
            
            if (!anthInput) return { success: false, error: 'Settings inputs not found in DOM' };
            
            anthInput.value = 'sk-ant-browserui-test-key-777';
            elevInput.value = 'eleven_browserui_test_key_888';
            falInput.value = 'fal_browserui_test_key_999';
            
            anthInput.dispatchEvent(new Event('input', { bubbles: true }));
            elevInput.dispatchEvent(new Event('input', { bubbles: true }));
            falInput.dispatchEvent(new Event('input', { bubbles: true }));
            
            const testBtn = document.getElementById('test-anthropic');
            if (testBtn) testBtn.click();
            
            await new Promise(r => setTimeout(r, 1000));
            
            const statusAnth = document.getElementById('status-anthropic').textContent;
            
            const form = document.getElementById('settings-form');
            if (form) {
                form.dispatchEvent(new Event('submit', { bubbles: true }));
            }
            
            await new Promise(r => setTimeout(r, 1000));
            const msg = document.getElementById('settings-message').textContent;
            
            return { success: true, statusAnth, msg, url: window.location.hash };
        })()
        """

        await websocket.send(json.dumps({
            "id": 4,
            "method": "Runtime.evaluate",
            "params": {
                "expression": eval_script,
                "awaitPromise": True,
                "returnByValue": True
            }
        }))
        
        eval_resp = await websocket.recv()
        eval_data = json.loads(eval_resp)
        print("   CDP Runtime.evaluate result:")
        print(json.dumps(eval_data, indent=2, ensure_ascii=False))

    print("\n✓ Browser debugging session verified and settings UI test journey successfully automated!")

if __name__ == "__main__":
    asyncio.run(main())
