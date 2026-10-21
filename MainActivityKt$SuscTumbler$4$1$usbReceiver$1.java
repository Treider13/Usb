package ru.cyclone.susc_tumbler;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.hardware.usb.UsbDevice;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import androidx.compose.runtime.MutableState;
import com.hoho.android.usbserial.driver.UsbSerialDriver;
import com.hoho.android.usbserial.driver.UsbSerialPort;
import java.util.List;
import kotlin.Metadata;
import kotlin.jvm.internal.Intrinsics;

/* JADX INFO: compiled from: MainActivity.kt */
/* JADX INFO: loaded from: /tmp/decompiler/1fff03f604024d51870ca7c74eae34df/classes2.dex */
@Metadata(d1 = {"\u0000\u001d\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000*\u0001\u0000\b\n\u0018\u00002\u00020\u0001J\u0018\u0010\u0002\u001a\u00020\u00032\u0006\u0010\u0004\u001a\u00020\u00052\u0006\u0010\u0006\u001a\u00020\u0007H\u0016¨\u0006\b"}, d2 = {"ru/cyclone/susc_tumbler/MainActivityKt$SuscTumbler$4$1$usbReceiver$1", "Landroid/content/BroadcastReceiver;", "onReceive", "", "context", "Landroid/content/Context;", "intent", "Landroid/content/Intent;", "app_release"}, k = 1, mv = {2, 0, 0}, xi = 48)
public final class MainActivityKt$SuscTumbler$4$1$usbReceiver$1 extends BroadcastReceiver {
    final /* synthetic */ MutableState<List<UsbSerialPort>> $availablePorts$delegate;
    final /* synthetic */ MutableState<UsbSerialPort> $connectedPort$delegate;
    final /* synthetic */ Context $context;
    final /* synthetic */ MutableState<Boolean> $showPortDialog$delegate;
    final /* synthetic */ UsbSerialManager $usbSerialManager;

    MainActivityKt$SuscTumbler$4$1$usbReceiver$1(UsbSerialManager usbSerialManager, MutableState<Boolean> mutableState, Context context, MutableState<List<UsbSerialPort>> mutableState2, MutableState<UsbSerialPort> mutableState3) {
        this.$usbSerialManager = usbSerialManager;
        this.$showPortDialog$delegate = mutableState;
        this.$context = context;
        this.$availablePorts$delegate = mutableState2;
        this.$connectedPort$delegate = mutableState3;
    }

    @Override // android.content.BroadcastReceiver
    public void onReceive(Context context, Intent intent) {
        UsbDevice usbDevice;
        UsbSerialDriver driver;
        UsbDevice device;
        Intrinsics.checkNotNullParameter(context, "context");
        Intrinsics.checkNotNullParameter(intent, "intent");
        Handler handler = new Handler(Looper.getMainLooper());
        String action = intent.getAction();
        if (action != null) {
            int iHashCode = action.hashCode();
            if (iHashCode != -2114103349) {
                if (iHashCode != -1608292967) {
                    if (iHashCode == -1562908784 && action.equals("ru.cyclone.susc_tumbler.USB_PERMISSION_RESPONSE")) {
                        if (intent.getBooleanExtra("permission", false)) {
                            DebugLogger.INSTANCE.i("USB", "Permission granted. Please select the port again.");
                        } else {
                            DebugLogger.INSTANCE.i("USB", "Permission denied.");
                            MainActivityKt.SuscTumbler$lambda$8(this.$showPortDialog$delegate, false);
                        }
                        MainActivityKt.SuscTumbler$refreshDeviceList(this.$context, this.$usbSerialManager, this.$availablePorts$delegate, this.$showPortDialog$delegate, this.$connectedPort$delegate);
                        return;
                    }
                    return;
                }
                if (!action.equals("android.hardware.usb.action.USB_DEVICE_DETACHED")) {
                    return;
                }
            } else if (!action.equals("android.hardware.usb.action.USB_DEVICE_ATTACHED")) {
                return;
            }
            DebugLogger.INSTANCE.i("USB", "Device state changed.");
            if (Build.VERSION.SDK_INT >= 33) {
                usbDevice = (UsbDevice) intent.getParcelableExtra("device", UsbDevice.class);
            } else {
                usbDevice = (UsbDevice) intent.getParcelableExtra("device");
            }
            Integer numValueOf = usbDevice != null ? Integer.valueOf(usbDevice.getDeviceId()) : null;
            UsbSerialPort usbSerialPortSuscTumbler$lambda$4 = MainActivityKt.SuscTumbler$lambda$4(this.$connectedPort$delegate);
            if (Intrinsics.areEqual(numValueOf, (usbSerialPortSuscTumbler$lambda$4 == null || (driver = usbSerialPortSuscTumbler$lambda$4.getDriver()) == null || (device = driver.getDevice()) == null) ? null : Integer.valueOf(device.getDeviceId()))) {
                this.$usbSerialManager.disconnect();
                this.$connectedPort$delegate.setValue(null);
            }
            final Context context2 = this.$context;
            final UsbSerialManager usbSerialManager = this.$usbSerialManager;
            final MutableState<List<UsbSerialPort>> mutableState = this.$availablePorts$delegate;
            final MutableState<Boolean> mutableState2 = this.$showPortDialog$delegate;
            final MutableState<UsbSerialPort> mutableState3 = this.$connectedPort$delegate;
            handler.postDelayed(new Runnable() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$4$1$usbReceiver$1$$ExternalSyntheticLambda0
                @Override // java.lang.Runnable
                public final void run() {
                    MainActivityKt.access$SuscTumbler$refreshDeviceList(context2, usbSerialManager, mutableState, mutableState2, mutableState3);
                }
            }, 500L);
        }
    }
}
