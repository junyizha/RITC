package com.company;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import org.json.*;

public class Main {

    public static void main(String[] args) {
        getTick();
    }

    public static int getTick() {
        try {
            URL tickurl = new URL("http://localhost:9999/v1/case");
            HttpURLConnection conn = (HttpURLConnection) tickurl.openConnection();
            conn.setRequestMethod("GET");
            String apiKey = "KN0P68A7";
            conn.setRequestProperty("X-API-Key", apiKey);
            if (conn.getResponseCode() != 200) {
                throw new RuntimeException("Failed : HTTP Error code : " + conn.getResponseCode());
            }
            InputStreamReader in = new InputStreamReader(conn.getInputStream());
            BufferedReader br = new BufferedReader(in);
            String output;
            while ((output = br.readLine()) != null) {
                JSONObject obj = new JSONObject(output);
                System.out.println(output);
                System.out.println(obj);
            }
            conn.disconnect();
        } catch (Exception e) {
            System.out.println("Exception in NetClientGet:- " + e);
        }
        return 0;
    }

}
