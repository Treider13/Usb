package ru.cyclone.susc_tumbler;

import androidx.compose.runtime.MutableFloatState;
import androidx.compose.runtime.MutableState;
import kotlin.Metadata;
import kotlin.Pair;
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
@DebugMetadata(c = "ru.cyclone.susc_tumbler.MainActivityKt$SuscTumblerContent$1$1$1", f = "MainActivity.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, s = {})
final class MainActivityKt$SuscTumblerContent$1$1$1 extends SuspendLambda implements Function2<CoroutineScope, Continuation<? super Unit>, Object> {
    final /* synthetic */ Pair<String, Integer> $lastReceivedValue;
    final /* synthetic */ MutableState<Boolean> $ledState$delegate;
    final /* synthetic */ MutableFloatState $sliderPosition$delegate;
    final /* synthetic */ MutableState<Boolean> $switchBW$delegate;
    int label;

    /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
    MainActivityKt$SuscTumblerContent$1$1$1(Pair<String, Integer> pair, MutableState<Boolean> mutableState, MutableFloatState mutableFloatState, MutableState<Boolean> mutableState2, Continuation<? super MainActivityKt$SuscTumblerContent$1$1$1> continuation) {
        super(2, continuation);
        this.$lastReceivedValue = pair;
        this.$ledState$delegate = mutableState;
        this.$sliderPosition$delegate = mutableFloatState;
        this.$switchBW$delegate = mutableState2;
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final Continuation<Unit> create(Object obj, Continuation<?> continuation) {
        return new MainActivityKt$SuscTumblerContent$1$1$1(this.$lastReceivedValue, this.$ledState$delegate, this.$sliderPosition$delegate, this.$switchBW$delegate, continuation);
    }

    @Override // kotlin.jvm.functions.Function2
    public final Object invoke(CoroutineScope coroutineScope, Continuation<? super Unit> continuation) {
        return ((MainActivityKt$SuscTumblerContent$1$1$1) create(coroutineScope, continuation)).invokeSuspend(Unit.INSTANCE);
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final Object invokeSuspend(Object obj) {
        IntrinsicsKt.getCOROUTINE_SUSPENDED();
        if (this.label != 0) {
            throw new IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
        ResultKt.throwOnFailure(obj);
        Pair<String, Integer> pair = this.$lastReceivedValue;
        if (pair != null) {
            MutableState<Boolean> mutableState = this.$ledState$delegate;
            MutableFloatState mutableFloatState = this.$sliderPosition$delegate;
            MutableState<Boolean> mutableState2 = this.$switchBW$delegate;
            DebugLogger.INSTANCE.i("SUSC_TUMBLER", "--------\nRegistry name: " + ((Object) pair.getFirst()) + ", \nValue: " + pair.getSecond() + "\n--------");
            String first = pair.getFirst();
            int iHashCode = first.hashCode();
            if (iHashCode != -1180143777) {
                if (iHashCode != 77742365) {
                    if (iHashCode == 517430135 && first.equals("USER_LED")) {
                        MainActivityKt.SuscTumblerContent$lambda$45$lambda$31(mutableState, pair.getSecond().intValue() == 1);
                    }
                } else if (first.equals("RANGE")) {
                    MainActivityKt.SuscTumblerContent$lambda$45$lambda$34(mutableState2, pair.getSecond().intValue() == 1);
                }
            } else if (first.equals("SS_RATE")) {
                mutableFloatState.setFloatValue(pair.getSecond().intValue());
            }
        }
        return Unit.INSTANCE;
    }
}
