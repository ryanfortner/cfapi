Java.perform(function () {
    console.log("[*] Starting Crypto Hooks...");

    var SecretKeySpec = Java.use('javax.crypto.spec.SecretKeySpec');

    // Hook the SecretKeySpec constructor: SecretKeySpec(byte[] key, String algorithm)
    SecretKeySpec.$init.overload('[B', 'java.lang.String').implementation = function (keyBytes, algorithm) {
        
        // Call the original constructor
        this.$init(keyBytes, algorithm);

        // We are only interested in HMAC/HS512 keys
        if (algorithm.indexOf("Hmac") !== -1 || algorithm.indexOf("HS512") !== -1) {
            console.log("\n[+] SecretKeySpec Initialized!");
            console.log("[-] Algorithm: " + algorithm);
            
            // Convert the byte array to a readable hex string
            var keyHex = "";
            for (var i = 0; i < keyBytes.length; i++) {
                var hex = (keyBytes[i] & 0xFF).toString(16);
                if (hex.length === 1) hex = "0" + hex;
                keyHex += hex;
            }
            console.log("[-] Key (Hex): " + keyHex);
            
            // Attempt to print as plain text (ASCII) if possible
            try {
                var StringClass = Java.use('java.lang.String');
                var plainTextKey = StringClass.$new(keyBytes);
                console.log("[-] Key (String): " + plainTextKey);
            } catch (e) {
                console.log("[-] Key is not a printable string.");
            }
        }
    };
});
