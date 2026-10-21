package ru.cyclone.susc_tumbler;

import android.content.Context;
import androidx.compose.runtime.MutableState;
import com.hoho.android.usbserial.driver.UsbSerialPort;
import java.util.List;
import kotlin.Metadata;
import kotlin.ResultKt;
import kotlin.Unit;
import kotlin.coroutines.Continuation;
import kotlin.coroutines.intrinsics.IntrinsicsKt;
import kotlin.coroutines.jvm.internal.DebugMetadata;
import kotlin.coroutines.jvm.internal.SuspendLambda;
import kotlin.jvm.functions.Function2;
import kotlinx.coroutines.CoroutineScope;

/* JADX INFO: compiled from: MainActivity.kt */
/* JADX INFO: loaded from: /tmp/decompiler/1fff03f604024d51870ca7c74eae34df/classes2.dex */
@Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lkotlinx/coroutines/CoroutineScope;"}, k = 3, mv = {2, 0, 0}, xi = 48)
@DebugMetadata(c = "ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$3$1", f = "MainActivity.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, s = {})
final class MainActivityKt$SuscTumbler$3$1 extends SuspendLambda implements Function2<CoroutineScope, Continuation<? super Unit>, Object> {
    final /* synthetic */ MutableState<List<UsbSerialPort>> $availablePorts$delegate;
    final /* synthetic */ MutableState<UsbSerialPort> $connectedPort$delegate;
    final /* synthetic */ Context $context;
    final /* synthetic */ MutableState<Boolean> $showPortDialog$delegate;
    final /* synthetic */ UsbSerialManager $usbSerialManager;
    int label;

    /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
    MainActivityKt$SuscTumbler$3$1(Context context, UsbSerialManager usbSerialManager, MutableState<List<UsbSerialPort>> mutableState, MutableState<Boolean> mutableState2, MutableState<UsbSerialPort> mutableState3, Continuation<? super MainActivityKt$SuscTumbler$3$1> continuation) {
        super(2, continuation);
        this.$context = context;
        this.$usbSerialManager = usbSerialManager;
        this.$availablePorts$delegate = mutableState;
        this.$showPortDialog$delegate = mutableState2;
        this.$connectedPort$delegate = mutableState3;
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final Continuation<Unit> create(Object obj, Continuation<?> continuation) {
        return new MainActivityKt$SuscTumbler$3$1(this.$context, this.$usbSerialManager, this.$availablePorts$delegate, this.$showPortDialog$delegate, this.$connectedPort$delegate, continuation);
    }

    @Override // kotlin.jvm.functions.Function2
    public final Object invoke(CoroutineScope coroutineScope, Continuation<? super Unit> continuation) {
        return ((MainActivityKt$SuscTumbler$3$1) create(coroutineScope, continuation)).invokeSuspend(Unit.INSTANCE);
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final Object invokeSuspend(Object obj) {
        IntrinsicsKt.getCOROUTINE_SUSPENDED();
        if (this.label == 0) {
            ResultKt.throwOnFailure(obj);
            MainActivityKt.SuscTumbler$refreshDeviceList(this.$context, this.$usbSerialManager, this.$availablePorts$delegate, this.$showPortDialog$delegate, this.$connectedPort$delegate);
            return Unit.INSTANCE;
        }
        throw new IllegalStateException("call to 'resume' before 'invoke' with coroutine");
    }
}
