package ru.cyclone.susc_tumbler;

import android.content.Context;
import android.hardware.usb.UsbDeviceConnection;
import android.hardware.usb.UsbManager;
import com.hoho.android.usbserial.driver.UsbSerialPort;
import com.hoho.android.usbserial.util.SerialInputOutputManager;
import java.io.IOException;
import java.util.concurrent.atomic.AtomicBoolean;
import kotlin.Metadata;
import kotlin.jvm.internal.Intrinsics;
import kotlinx.coroutines.flow.FlowKt;
import kotlinx.coroutines.flow.MutableStateFlow;
import kotlinx.coroutines.flow.StateFlow;
import kotlinx.coroutines.flow.StateFlowKt;

/* JADX INFO: compiled from: UsbSerialManager.kt */
/* JADX INFO: loaded from: /tmp/decompiler/1fff03f604024d51870ca7c74eae34df/classes2.dex */
@Metadata(d1 = {"\u0000T\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\u0010\u0012\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u000b\n\u0000\n\u0002\u0010\u0002\n\u0002\b\b\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\b\u0007\u0018\u00002\u00020\u0001B\u000f\u0012\u0006\u0010\u0002\u001a\u00020\u0003¢\u0006\u0004\b\u0004\u0010\u0005J\u0006\u0010\u0015\u001a\u00020\u0016J\u000e\u0010\u0017\u001a\u00020\u00182\u0006\u0010\u0019\u001a\u00020\u000eJ\u0006\u0010\u001a\u001a\u00020\u0018J\u000e\u0010\u001b\u001a\u00020\u00182\u0006\u0010\u001c\u001a\u00020\bJ\u0010\u0010\u001d\u001a\u00020\u00182\u0006\u0010\u001c\u001a\u00020\bH\u0016J\u0006\u0010\u001e\u001a\u00020\u0018J\u0014\u0010\u001f\u001a\u00020\u00182\n\u0010 \u001a\u00060!j\u0002`\"H\u0016R\u000e\u0010\u0002\u001a\u00020\u0003X\u0082\u0004¢\u0006\u0002\n\u0000R\u0016\u0010\u0006\u001a\n\u0012\u0006\u0012\u0004\u0018\u00010\b0\u0007X\u0082\u0004¢\u0006\u0002\n\u0000R\u0019\u0010\t\u001a\n\u0012\u0006\u0012\u0004\u0018\u00010\b0\n¢\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\fR\u0010\u0010\r\u001a\u0004\u0018\u00010\u000eX\u0082\u000e¢\u0006\u0002\n\u0000R\u0010\u0010\u000f\u001a\u0004\u0018\u00010\u0010X\u0082\u000e¢\u0006\u0002\n\u0000R\u0010\u0010\u0011\u001a\u0004\u0018\u00010\u0012X\u0082\u000e¢\u0006\u0002\n\u0000R\u000e\u0010\u0013\u001a\u00020\u0014X\u0082\u0004¢\u0006\u0002\n\u0000¨\u0006#"}, d2 = {"Lru/cyclone/susc_tumbler/UsbSerialManager;", "Lcom/hoho/android/usbserial/util/SerialInputOutputManager$Listener;", "context", "Landroid/content/Context;", "<init>", "(Landroid/content/Context;)V", "_receivedDataFlow", "Lkotlinx/coroutines/flow/MutableStateFlow;", "", "receivedDataFlow", "Lkotlinx/coroutines/flow/StateFlow;", "getReceivedDataFlow", "()Lkotlinx/coroutines/flow/StateFlow;", "port", "Lcom/hoho/android/usbserial/driver/UsbSerialPort;", "connection", "Landroid/hardware/usb/UsbDeviceConnection;", "serialInputOutputManager", "Lcom/hoho/android/usbserial/util/SerialInputOutputManager;", "isConnectingOrConnected", "Ljava/util/concurrent/atomic/AtomicBoolean;", "isConnected", "", "connect", "", "selectedPort", "disconnect", "write", "data", "onNewData", "resetReceivedData", "onRunError", "e", "Ljava/lang/Exception;", "Lkotlin/Exception;", "app_release"}, k = 1, mv = {2, 0, 0}, xi = 48)
public final class UsbSerialManager implements SerialInputOutputManager.Listener {
    public static final int $stable = 8;
    private final MutableStateFlow<byte[]> _receivedDataFlow;
    private UsbDeviceConnection connection;
    private final Context context;
    private final AtomicBoolean isConnectingOrConnected;
    private UsbSerialPort port;
    private final StateFlow<byte[]> receivedDataFlow;
    private SerialInputOutputManager serialInputOutputManager;

    public UsbSerialManager(Context context) {
        Intrinsics.checkNotNullParameter(context, "context");
        this.context = context;
        MutableStateFlow<byte[]> MutableStateFlow = StateFlowKt.MutableStateFlow(null);
        this._receivedDataFlow = MutableStateFlow;
        this.receivedDataFlow = FlowKt.asStateFlow(MutableStateFlow);
        this.isConnectingOrConnected = new AtomicBoolean(false);
    }

    public final StateFlow<byte[]> getReceivedDataFlow() {
        return this.receivedDataFlow;
    }

    public final boolean isConnected() {
        return this.isConnectingOrConnected.get();
    }

    public final void connect(final UsbSerialPort selectedPort) {
        UsbSerialPort usbSerialPort;
        Intrinsics.checkNotNullParameter(selectedPort, "selectedPort");
        if (isConnected() && (usbSerialPort = this.port) != null && usbSerialPort.getPortNumber() == selectedPort.getPortNumber()) {
            return;
        }
        new Thread(new Runnable() { // from class: ru.cyclone.susc_tumbler.UsbSerialManager$$ExternalSyntheticLambda0
            @Override // java.lang.Runnable
            public final void run() {
                UsbSerialManager.connect$lambda$0(this.f$0, selectedPort);
            }
        }).start();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final void connect$lambda$0(UsbSerialManager usbSerialManager, UsbSerialPort usbSerialPort) {
        Object systemService = usbSerialManager.context.getSystemService("usb");
        Intrinsics.checkNotNull(systemService, "null cannot be cast to non-null type android.hardware.usb.UsbManager");
        UsbManager usbManager = (UsbManager) systemService;
        if (usbManager.hasPermission(usbSerialPort.getDriver().getDevice())) {
            try {
                usbSerialManager.isConnectingOrConnected.set(true);
                UsbDeviceConnection usbDeviceConnectionOpenDevice = usbManager.openDevice(usbSerialPort.getDriver().getDevice());
                usbSerialManager.connection = usbDeviceConnectionOpenDevice;
                if (usbDeviceConnectionOpenDevice == null) {
                    usbSerialManager.disconnect();
                    return;
                }
                usbSerialManager.port = usbSerialPort;
                Intrinsics.checkNotNull(usbSerialPort);
                usbSerialPort.open(usbSerialManager.connection);
                UsbSerialPort usbSerialPort2 = usbSerialManager.port;
                Intrinsics.checkNotNull(usbSerialPort2);
                usbSerialPort2.setParameters(115200, 8, 1, 0);
                SerialInputOutputManager serialInputOutputManager = new SerialInputOutputManager(usbSerialManager.port, usbSerialManager);
                usbSerialManager.serialInputOutputManager = serialInputOutputManager;
                Intrinsics.checkNotNull(serialInputOutputManager);
                serialInputOutputManager.start();
            } catch (Exception e) {
                e.printStackTrace();
                usbSerialManager.disconnect();
            }
        }
    }

    public final void disconnect() {
        this.isConnectingOrConnected.set(false);
        try {
            SerialInputOutputManager serialInputOutputManager = this.serialInputOutputManager;
            if (serialInputOutputManager != null) {
                serialInputOutputManager.stop();
            }
            this.serialInputOutputManager = null;
            UsbSerialPort usbSerialPort = this.port;
            if (usbSerialPort != null) {
                usbSerialPort.close();
            }
            this.port = null;
        } catch (IOException e) {
            DebugLogger.INSTANCE.i("SerialManager", "Error closing port: " + e.getMessage());
        }
    }

    public final void write(byte[] data) {
        Intrinsics.checkNotNullParameter(data, "data");
        UsbSerialPort usbSerialPort = this.port;
        if (usbSerialPort == null || this.serialInputOutputManager == null || usbSerialPort == null) {
            return;
        }
        try {
            usbSerialPort.write(data, 0);
        } catch (IOException e) {
            DebugLogger.INSTANCE.i("SerialManager", "Error writing data: " + e.getMessage());
        }
    }

    @Override // com.hoho.android.usbserial.util.SerialInputOutputManager.Listener
    public void onNewData(byte[] data) {
        Intrinsics.checkNotNullParameter(data, "data");
        this._receivedDataFlow.setValue(data);
    }

    public final void resetReceivedData() {
        this._receivedDataFlow.setValue(null);
    }

    @Override // com.hoho.android.usbserial.util.SerialInputOutputManager.Listener
    public void onRunError(Exception e) {
        Intrinsics.checkNotNullParameter(e, "e");
        DebugLogger.INSTANCE.i("SerialManager", "Listener error: " + e.getMessage());
        disconnect();
    }
}
