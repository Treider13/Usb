package ru.cyclone.susc_tumbler;

import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.hardware.usb.UsbManager;
import android.os.Build;
import androidx.compose.foundation.BorderStroke;
import androidx.compose.foundation.ClickableKt;
import androidx.compose.foundation.ImageKt;
import androidx.compose.foundation.interaction.MutableInteractionSource;
import androidx.compose.foundation.layout.Arrangement;
import androidx.compose.foundation.layout.ColumnKt;
import androidx.compose.foundation.layout.ColumnScope;
import androidx.compose.foundation.layout.ColumnScopeInstance;
import androidx.compose.foundation.layout.PaddingKt;
import androidx.compose.foundation.layout.PaddingValues;
import androidx.compose.foundation.layout.SizeKt;
import androidx.compose.foundation.layout.SpacerKt;
import androidx.compose.foundation.layout.WindowInsets;
import androidx.compose.foundation.layout.WindowInsetsPadding_androidKt;
import androidx.compose.material3.ButtonColors;
import androidx.compose.material3.ButtonElevation;
import androidx.compose.material3.ButtonKt;
import androidx.compose.material3.CardColors;
import androidx.compose.material3.CardDefaults;
import androidx.compose.material3.CardElevation;
import androidx.compose.material3.CardKt;
import androidx.compose.material3.MaterialTheme;
import androidx.compose.material3.ProgressIndicatorKt;
import androidx.compose.material3.ScaffoldKt;
import androidx.compose.material3.SliderColors;
import androidx.compose.material3.SliderKt;
import androidx.compose.material3.SnackbarHostKt;
import androidx.compose.material3.SnackbarHostState;
import androidx.compose.material3.TextKt;
import androidx.compose.runtime.Applier;
import androidx.compose.runtime.ComposablesKt;
import androidx.compose.runtime.Composer;
import androidx.compose.runtime.ComposerKt;
import androidx.compose.runtime.CompositionLocal;
import androidx.compose.runtime.CompositionLocalMap;
import androidx.compose.runtime.CompositionScopedCoroutineScopeCanceller;
import androidx.compose.runtime.DisposableEffectResult;
import androidx.compose.runtime.DisposableEffectScope;
import androidx.compose.runtime.EffectsKt;
import androidx.compose.runtime.FloatState;
import androidx.compose.runtime.MutableFloatState;
import androidx.compose.runtime.MutableState;
import androidx.compose.runtime.PrimitiveSnapshotStateKt;
import androidx.compose.runtime.RecomposeScopeImplKt;
import androidx.compose.runtime.ScopeUpdateScope;
import androidx.compose.runtime.SnapshotMutationPolicy;
import androidx.compose.runtime.SnapshotStateKt;
import androidx.compose.runtime.State;
import androidx.compose.runtime.Updater;
import androidx.compose.runtime.internal.ComposableLambdaKt;
import androidx.compose.ui.Alignment;
import androidx.compose.ui.ComposedModifierKt;
import androidx.compose.ui.Modifier;
import androidx.compose.ui.graphics.ColorFilter;
import androidx.compose.ui.graphics.Shape;
import androidx.compose.ui.layout.ContentScale;
import androidx.compose.ui.layout.MeasurePolicy;
import androidx.compose.ui.node.ComposeUiNode;
import androidx.compose.ui.platform.AndroidCompositionLocals_androidKt;
import androidx.compose.ui.res.PainterResources_androidKt;
import androidx.compose.ui.res.StringResources_androidKt;
import androidx.compose.ui.semantics.Role;
import androidx.compose.ui.text.TextStyle;
import androidx.compose.ui.text.font.FontFamily;
import androidx.compose.ui.text.font.FontStyle;
import androidx.compose.ui.text.font.FontWeight;
import androidx.compose.ui.text.style.TextAlign;
import androidx.compose.ui.text.style.TextDecoration;
import androidx.compose.ui.unit.Dp;
import androidx.compose.ui.window.AndroidDialog_androidKt;
import androidx.compose.ui.window.DialogProperties;
import androidx.core.content.ContextCompat;
import androidx.core.view.accessibility.AccessibilityEventCompat;
import androidx.profileinstaller.ProfileVerifier;
import com.hoho.android.usbserial.driver.UsbSerialDriver;
import com.hoho.android.usbserial.driver.UsbSerialPort;
import com.hoho.android.usbserial.driver.UsbSerialProber;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import kotlin.Metadata;
import kotlin.Pair;
import kotlin.Unit;
import kotlin.collections.CollectionsKt;
import kotlin.coroutines.Continuation;
import kotlin.coroutines.CoroutineContext;
import kotlin.coroutines.EmptyCoroutineContext;
import kotlin.coroutines.intrinsics.IntrinsicsKt;
import kotlin.jvm.functions.Function0;
import kotlin.jvm.functions.Function1;
import kotlin.jvm.functions.Function2;
import kotlin.jvm.functions.Function3;
import kotlin.jvm.internal.Intrinsics;
import kotlin.ranges.ClosedFloatingPointRange;
import kotlin.ranges.RangesKt;
import kotlinx.coroutines.BuildersKt__Builders_commonKt;
import kotlinx.coroutines.CoroutineScope;
import ru.cyclone.susc_tumbler.MainActivityKt;
import ru.cyclone.susc_tumbler.ui.theme.ThemeKt;

/* JADX INFO: compiled from: MainActivity.kt */
/* JADX INFO: loaded from: /tmp/decompiler/1fff03f604024d51870ca7c74eae34df/classes2.dex */
@Metadata(d1 = {"\u0000Z\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0003\n\u0002\u0010\t\n\u0002\b\u0002\n\u0002\u0010\u0002\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0010\b\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\b\u0007\n\u0002\u0010\u0012\n\u0002\b\u0003\n\u0002\u0010\u0007\u001a\r\u0010\u0007\u001a\u00020\bH\u0007¢\u0006\u0002\u0010\t\u001a=\u0010\n\u001a\u00020\b2\f\u0010\u000b\u001a\b\u0012\u0004\u0012\u00020\r0\f2\u0012\u0010\u000e\u001a\u000e\u0012\u0004\u0012\u00020\r\u0012\u0004\u0012\u00020\b0\u000f2\f\u0010\u0010\u001a\b\u0012\u0004\u0012\u00020\b0\u0011H\u0007¢\u0006\u0002\u0010\u0012\u001a\u0087\u0001\u0010\u0013\u001a\u00020\b2\u0006\u0010\u0014\u001a\u00020\u00152\u0006\u0010\u0016\u001a\u00020\u00152\u0014\u0010\u0017\u001a\u0010\u0012\u0004\u0012\u00020\u0001\u0012\u0004\u0012\u00020\u0019\u0018\u00010\u00182\u0012\u0010\u001a\u001a\u000e\u0012\u0004\u0012\u00020\u0019\u0012\u0004\u0012\u00020\b0\u000f2\f\u0010\u001b\u001a\b\u0012\u0004\u0012\u00020\b0\u00112\u0012\u0010\u001c\u001a\u000e\u0012\u0004\u0012\u00020\u0015\u0012\u0004\u0012\u00020\b0\u000f2\u0012\u0010\u001d\u001a\u000e\u0012\u0004\u0012\u00020\u0015\u0012\u0004\u0012\u00020\b0\u000f2\b\b\u0002\u0010\u001e\u001a\u00020\u001fH\u0007¢\u0006\u0002\u0010 \u001a\r\u0010!\u001a\u00020\bH\u0007¢\u0006\u0002\u0010\t\"\u000e\u0010\u0000\u001a\u00020\u0001X\u0082T¢\u0006\u0002\n\u0000\"\u000e\u0010\u0002\u001a\u00020\u0001X\u0082T¢\u0006\u0002\n\u0000\"\u000e\u0010\u0003\u001a\u00020\u0001X\u0082T¢\u0006\u0002\n\u0000\"\u000e\u0010\u0004\u001a\u00020\u0005X\u0082T¢\u0006\u0002\n\u0000\"\u000e\u0010\u0006\u001a\u00020\u0005X\u0082T¢\u0006\u0002\n\u0000¨\u0006\"²\u0006\u0010\u0010#\u001a\b\u0012\u0004\u0012\u00020\r0\fX\u008a\u008e\u0002²\u0006\f\u0010$\u001a\u0004\u0018\u00010\rX\u008a\u008e\u0002²\u0006\n\u0010%\u001a\u00020\u0015X\u008a\u008e\u0002²\u0006\n\u0010\u0016\u001a\u00020\u0015X\u008a\u008e\u0002²\u0006\f\u0010&\u001a\u0004\u0018\u00010'X\u008a\u0084\u0002²\u0006\n\u0010(\u001a\u00020\u0015X\u008a\u008e\u0002²\u0006\n\u0010)\u001a\u00020\u0015X\u008a\u008e\u0002²\u0006\n\u0010*\u001a\u00020+X\u008a\u008e\u0002"}, d2 = {"ACTION_USB_PERMISSION_RESPONSE", "", "MAIN_LOG_TAG", "USB_LOG_TAG", "INITIALIZATION_TIMEOUT", "", "CHECK_TIMEOUT", "SuscTumbler", "", "(Landroidx/compose/runtime/Composer;I)V", "PortSelectionDialog", "ports", "", "Lcom/hoho/android/usbserial/driver/UsbSerialPort;", "onPortSelected", "Lkotlin/Function1;", "onDismiss", "Lkotlin/Function0;", "(Ljava/util/List;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function0;Landroidx/compose/runtime/Composer;I)V", "SuscTumblerContent", "isDeviceConnected", "", "isDevicePowerOn", "lastReceivedValue", "Lkotlin/Pair;", "", "onChangeRequest", "onWriteRequest", "onLEDRequest", "onRangeRequest", "modifier", "Landroidx/compose/ui/Modifier;", "(ZZLkotlin/Pair;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function0;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Landroidx/compose/ui/Modifier;Landroidx/compose/runtime/Composer;II)V", "FullAppPreview", "app_release", "availablePorts", "connectedPort", "showPortDialog", "receivedData", "", "ledState", "switchBW", "sliderPosition", ""}, k = 2, mv = {2, 0, 0}, xi = 48)
public final class MainActivityKt {
    private static final String ACTION_USB_PERMISSION_RESPONSE = "ru.cyclone.susc_tumbler.USB_PERMISSION_RESPONSE";
    private static final long CHECK_TIMEOUT = 3000;
    private static final long INITIALIZATION_TIMEOUT = 500;
    private static final String MAIN_LOG_TAG = "SUSC_TUMBLER";
    private static final String USB_LOG_TAG = "USB";

    /* JADX INFO: Access modifiers changed from: private */
    public static final Unit FullAppPreview$lambda$47(int i, Composer composer, int i2) {
        FullAppPreview(composer, RecomposeScopeImplKt.updateChangedFlags(i | 1));
        return Unit.INSTANCE;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final Unit PortSelectionDialog$lambda$28(List list, Function1 function1, Function0 function0, int i, Composer composer, int i2) {
        PortSelectionDialog(list, function1, function0, composer, RecomposeScopeImplKt.updateChangedFlags(i | 1));
        return Unit.INSTANCE;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final Unit SuscTumbler$lambda$27(int i, Composer composer, int i2) {
        SuscTumbler(composer, RecomposeScopeImplKt.updateChangedFlags(i | 1));
        return Unit.INSTANCE;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final Unit SuscTumblerContent$lambda$46(boolean z, boolean z2, Pair pair, Function1 function1, Function0 function0, Function1 function12, Function1 function13, Modifier modifier, int i, int i2, Composer composer, int i3) {
        SuscTumblerContent(z, z2, pair, function1, function0, function12, function13, modifier, composer, RecomposeScopeImplKt.updateChangedFlags(i | 1), i2);
        return Unit.INSTANCE;
    }

    public static final void SuscTumbler(Composer composer, final int i) {
        MutableState mutableState;
        final MutableState mutableState2;
        final UsbSerialManager usbSerialManager;
        MainActivityKt$SuscTumbler$3$1 mainActivityKt$SuscTumbler$3$1;
        Composer composerStartRestartGroup = composer.startRestartGroup(1799781229);
        ComposerKt.sourceInformation(composerStartRestartGroup, "C(SuscTumbler)97@3839L7,98@3873L61,99@3960L49,100@4036L34,101@4098L34,102@4160L38,103@4257L16,105@4308L183,105@4279L212,141@5669L969,141@5639L999,199@8001L35,199@7980L56,205@8129L2542,205@8106L2565,271@10975L24,272@11028L32,275@11128L127,279@11262L2490,274@11095L2657:MainActivity.kt#6o5wwo");
        if (i != 0 || !composerStartRestartGroup.getSkipping()) {
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventStart(1799781229, i, -1, "ru.cyclone.susc_tumbler.SuscTumbler (MainActivity.kt:96)");
            }
            CompositionLocal localContext = AndroidCompositionLocals_androidKt.getLocalContext();
            ComposerKt.sourceInformationMarkerStart(composerStartRestartGroup, 2023513938, "CC:CompositionLocal.kt#9igjgp");
            Object objConsume = composerStartRestartGroup.consume(localContext);
            ComposerKt.sourceInformationMarkerEnd(composerStartRestartGroup);
            final Context context = (Context) objConsume;
            composerStartRestartGroup.startReplaceGroup(-316382040);
            ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
            Object objRememberedValue = composerStartRestartGroup.rememberedValue();
            if (objRememberedValue == Composer.Companion.getEmpty()) {
                objRememberedValue = SnapshotStateKt.mutableStateOf$default(CollectionsKt.emptyList(), (SnapshotMutationPolicy) null, 2, (Object) null);
                composerStartRestartGroup.updateRememberedValue(objRememberedValue);
            }
            MutableState mutableState3 = (MutableState) objRememberedValue;
            composerStartRestartGroup.endReplaceGroup();
            composerStartRestartGroup.startReplaceGroup(-316379268);
            ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
            Object objRememberedValue2 = composerStartRestartGroup.rememberedValue();
            if (objRememberedValue2 == Composer.Companion.getEmpty()) {
                objRememberedValue2 = SnapshotStateKt.mutableStateOf$default((Object) null, (SnapshotMutationPolicy) null, 2, (Object) null);
                composerStartRestartGroup.updateRememberedValue(objRememberedValue2);
            }
            final MutableState mutableState4 = (MutableState) objRememberedValue2;
            composerStartRestartGroup.endReplaceGroup();
            composerStartRestartGroup.startReplaceGroup(-316376851);
            ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
            Object objRememberedValue3 = composerStartRestartGroup.rememberedValue();
            if (objRememberedValue3 == Composer.Companion.getEmpty()) {
                objRememberedValue3 = SnapshotStateKt.mutableStateOf$default(false, (SnapshotMutationPolicy) null, 2, (Object) null);
                composerStartRestartGroup.updateRememberedValue(objRememberedValue3);
            }
            MutableState mutableState5 = (MutableState) objRememberedValue3;
            composerStartRestartGroup.endReplaceGroup();
            composerStartRestartGroup.startReplaceGroup(-316374867);
            ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
            Object objRememberedValue4 = composerStartRestartGroup.rememberedValue();
            if (objRememberedValue4 == Composer.Companion.getEmpty()) {
                objRememberedValue4 = SnapshotStateKt.mutableStateOf$default(false, (SnapshotMutationPolicy) null, 2, (Object) null);
                composerStartRestartGroup.updateRememberedValue(objRememberedValue4);
            }
            MutableState mutableState6 = (MutableState) objRememberedValue4;
            composerStartRestartGroup.endReplaceGroup();
            composerStartRestartGroup.startReplaceGroup(-316372879);
            ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
            Object objRememberedValue5 = composerStartRestartGroup.rememberedValue();
            if (objRememberedValue5 == Composer.Companion.getEmpty()) {
                objRememberedValue5 = new UsbSerialManager(context);
                composerStartRestartGroup.updateRememberedValue(objRememberedValue5);
            }
            UsbSerialManager usbSerialManager2 = (UsbSerialManager) objRememberedValue5;
            composerStartRestartGroup.endReplaceGroup();
            State stateCollectAsState = SnapshotStateKt.collectAsState(usbSerialManager2.getReceivedDataFlow(), (CoroutineContext) null, composerStartRestartGroup, 0, 1);
            byte[] bArrSuscTumbler$lambda$13 = SuscTumbler$lambda$13(stateCollectAsState);
            composerStartRestartGroup.startReplaceGroup(-316367998);
            ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
            boolean zChanged = composerStartRestartGroup.changed(stateCollectAsState);
            MainActivityKt$SuscTumbler$1$1 mainActivityKt$SuscTumbler$1$1RememberedValue = composerStartRestartGroup.rememberedValue();
            if (zChanged || mainActivityKt$SuscTumbler$1$1RememberedValue == Composer.Companion.getEmpty()) {
                mainActivityKt$SuscTumbler$1$1RememberedValue = new MainActivityKt$SuscTumbler$1$1(stateCollectAsState, mutableState6, null);
                composerStartRestartGroup.updateRememberedValue(mainActivityKt$SuscTumbler$1$1RememberedValue);
            }
            composerStartRestartGroup.endReplaceGroup();
            EffectsKt.LaunchedEffect(bArrSuscTumbler$lambda$13, (Function2) mainActivityKt$SuscTumbler$1$1RememberedValue, composerStartRestartGroup, 0);
            UsbSerialPort usbSerialPortSuscTumbler$lambda$4 = SuscTumbler$lambda$4(mutableState4);
            composerStartRestartGroup.startReplaceGroup(-316323660);
            ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
            boolean zChangedInstance = composerStartRestartGroup.changedInstance(usbSerialManager2);
            MainActivityKt$SuscTumbler$2$1 mainActivityKt$SuscTumbler$2$1RememberedValue = composerStartRestartGroup.rememberedValue();
            if (zChangedInstance || mainActivityKt$SuscTumbler$2$1RememberedValue == Composer.Companion.getEmpty()) {
                mainActivityKt$SuscTumbler$2$1RememberedValue = new MainActivityKt$SuscTumbler$2$1(usbSerialManager2, mutableState4, mutableState6, null);
                composerStartRestartGroup.updateRememberedValue(mainActivityKt$SuscTumbler$2$1RememberedValue);
            }
            composerStartRestartGroup.endReplaceGroup();
            EffectsKt.LaunchedEffect(usbSerialPortSuscTumbler$lambda$4, (Function2) mainActivityKt$SuscTumbler$2$1RememberedValue, composerStartRestartGroup, 0);
            Unit unit = Unit.INSTANCE;
            composerStartRestartGroup.startReplaceGroup(-316249970);
            ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
            boolean zChangedInstance2 = composerStartRestartGroup.changedInstance(context) | composerStartRestartGroup.changedInstance(usbSerialManager2);
            Object objRememberedValue6 = composerStartRestartGroup.rememberedValue();
            if (zChangedInstance2 || objRememberedValue6 == Composer.Companion.getEmpty()) {
                mutableState = mutableState3;
                mutableState2 = mutableState5;
                usbSerialManager = usbSerialManager2;
                mainActivityKt$SuscTumbler$3$1 = new MainActivityKt$SuscTumbler$3$1(context, usbSerialManager, mutableState, mutableState2, mutableState4, null);
                composerStartRestartGroup.updateRememberedValue(mainActivityKt$SuscTumbler$3$1);
            } else {
                mutableState = mutableState3;
                mainActivityKt$SuscTumbler$3$1 = objRememberedValue6;
                mutableState2 = mutableState5;
                usbSerialManager = usbSerialManager2;
            }
            composerStartRestartGroup.endReplaceGroup();
            EffectsKt.LaunchedEffect(unit, (Function2) mainActivityKt$SuscTumbler$3$1, composerStartRestartGroup, 6);
            DebugLogger.INSTANCE.i(MAIN_LOG_TAG, "Starting search usb devices");
            Unit unit2 = Unit.INSTANCE;
            composerStartRestartGroup.startReplaceGroup(-316243367);
            ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
            boolean zChangedInstance3 = composerStartRestartGroup.changedInstance(context) | composerStartRestartGroup.changedInstance(usbSerialManager);
            Object objRememberedValue7 = composerStartRestartGroup.rememberedValue();
            if (zChangedInstance3 || objRememberedValue7 == Composer.Companion.getEmpty()) {
                final MutableState mutableState7 = mutableState2;
                final MutableState mutableState8 = mutableState;
                Function1 function1 = new Function1() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$$ExternalSyntheticLambda0
                    @Override // kotlin.jvm.functions.Function1
                    public final Object invoke(Object obj) {
                        return MainActivityKt.SuscTumbler$lambda$21$lambda$20(context, usbSerialManager, mutableState7, mutableState8, mutableState4, (DisposableEffectScope) obj);
                    }
                };
                mutableState2 = mutableState7;
                mutableState = mutableState8;
                composerStartRestartGroup.updateRememberedValue(function1);
                objRememberedValue7 = function1;
            }
            composerStartRestartGroup.endReplaceGroup();
            EffectsKt.DisposableEffect(unit2, (Function1) objRememberedValue7, composerStartRestartGroup, 6);
            composerStartRestartGroup.startReplaceGroup(-316164093);
            ComposerKt.sourceInformation(composerStartRestartGroup, "263@10793L96,267@10915L26,261@10707L244");
            if (SuscTumbler$lambda$7(mutableState2)) {
                List<UsbSerialPort> listSuscTumbler$lambda$1 = SuscTumbler$lambda$1(mutableState);
                composerStartRestartGroup.startReplaceGroup(-316160565);
                ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
                boolean zChangedInstance4 = composerStartRestartGroup.changedInstance(context) | composerStartRestartGroup.changedInstance(usbSerialManager);
                Object objRememberedValue8 = composerStartRestartGroup.rememberedValue();
                if (zChangedInstance4 || objRememberedValue8 == Composer.Companion.getEmpty()) {
                    objRememberedValue8 = new Function1() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$$ExternalSyntheticLambda1
                        @Override // kotlin.jvm.functions.Function1
                        public final Object invoke(Object obj) {
                            return MainActivityKt.SuscTumbler$lambda$23$lambda$22(mutableState2, context, usbSerialManager, mutableState4, (UsbSerialPort) obj);
                        }
                    };
                    composerStartRestartGroup.updateRememberedValue(objRememberedValue8);
                }
                Function1 function12 = (Function1) objRememberedValue8;
                composerStartRestartGroup.endReplaceGroup();
                composerStartRestartGroup.startReplaceGroup(-316156731);
                ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
                Object objRememberedValue9 = composerStartRestartGroup.rememberedValue();
                if (objRememberedValue9 == Composer.Companion.getEmpty()) {
                    objRememberedValue9 = new Function0() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$$ExternalSyntheticLambda2
                        @Override // kotlin.jvm.functions.Function0
                        public final Object invoke() {
                            return MainActivityKt.SuscTumbler$lambda$25$lambda$24(mutableState2);
                        }
                    };
                    composerStartRestartGroup.updateRememberedValue(objRememberedValue9);
                }
                composerStartRestartGroup.endReplaceGroup();
                PortSelectionDialog(listSuscTumbler$lambda$1, function12, (Function0) objRememberedValue9, composerStartRestartGroup, 384);
            }
            composerStartRestartGroup.endReplaceGroup();
            ComposerKt.sourceInformationMarkerStart(composerStartRestartGroup, 773894976, "CC(rememberCoroutineScope)482@20332L144:Effects.kt#9igjgp");
            ComposerKt.sourceInformationMarkerStart(composerStartRestartGroup, -954367824, "CC(remember):Effects.kt#9igjgp");
            Object objRememberedValue10 = composerStartRestartGroup.rememberedValue();
            if (objRememberedValue10 == Composer.Companion.getEmpty()) {
                CompositionScopedCoroutineScopeCanceller compositionScopedCoroutineScopeCanceller = new CompositionScopedCoroutineScopeCanceller(EffectsKt.createCompositionCoroutineScope(EmptyCoroutineContext.INSTANCE, composerStartRestartGroup));
                composerStartRestartGroup.updateRememberedValue(compositionScopedCoroutineScopeCanceller);
                objRememberedValue10 = compositionScopedCoroutineScopeCanceller;
            }
            ComposerKt.sourceInformationMarkerEnd(composerStartRestartGroup);
            CoroutineScope coroutineScope = ((CompositionScopedCoroutineScopeCanceller) objRememberedValue10).getCoroutineScope();
            ComposerKt.sourceInformationMarkerEnd(composerStartRestartGroup);
            composerStartRestartGroup.startReplaceGroup(-316153109);
            ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
            Object objRememberedValue11 = composerStartRestartGroup.rememberedValue();
            if (objRememberedValue11 == Composer.Companion.getEmpty()) {
                objRememberedValue11 = new SnackbarHostState();
                composerStartRestartGroup.updateRememberedValue(objRememberedValue11);
            }
            final SnackbarHostState snackbarHostState = (SnackbarHostState) objRememberedValue11;
            composerStartRestartGroup.endReplaceGroup();
            ScaffoldKt.Scaffold-TvnljyQ((Modifier) null, (Function2) null, (Function2) null, ComposableLambdaKt.rememberComposableLambda(3466855, true, new Function2<Composer, Integer, Unit>() { // from class: ru.cyclone.susc_tumbler.MainActivityKt.SuscTumbler.7
                @Override // kotlin.jvm.functions.Function2
                public /* bridge */ /* synthetic */ Unit invoke(Composer composer2, Integer num) {
                    invoke(composer2, num.intValue());
                    return Unit.INSTANCE;
                }

                public final void invoke(Composer composer2, int i2) {
                    ComposerKt.sourceInformation(composer2, "C277@11202L43:MainActivity.kt#6o5wwo");
                    if ((i2 & 3) == 2 && composer2.getSkipping()) {
                        composer2.skipToGroupEnd();
                        return;
                    }
                    if (ComposerKt.isTraceInProgress()) {
                        ComposerKt.traceEventStart(3466855, i2, -1, "ru.cyclone.susc_tumbler.SuscTumbler.<anonymous> (MainActivity.kt:277)");
                    }
                    SnackbarHostKt.SnackbarHost(snackbarHostState, (Modifier) null, (Function3) null, composer2, 6, 6);
                    if (ComposerKt.isTraceInProgress()) {
                        ComposerKt.traceEventEnd();
                    }
                }
            }, composerStartRestartGroup, 54), (Function2) null, 0, 0L, 0L, (WindowInsets) null, ComposableLambdaKt.rememberComposableLambda(45429054, true, new AnonymousClass8(usbSerialManager, coroutineScope, mutableState4, mutableState6, stateCollectAsState, snackbarHostState), composerStartRestartGroup, 54), composerStartRestartGroup, 805309440, 503);
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventEnd();
            }
        } else {
            composerStartRestartGroup.skipToGroupEnd();
        }
        ScopeUpdateScope scopeUpdateScopeEndRestartGroup = composerStartRestartGroup.endRestartGroup();
        if (scopeUpdateScopeEndRestartGroup != null) {
            scopeUpdateScopeEndRestartGroup.updateScope(new Function2() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$$ExternalSyntheticLambda3
                @Override // kotlin.jvm.functions.Function2
                public final Object invoke(Object obj, Object obj2) {
                    return MainActivityKt.SuscTumbler$lambda$27(i, (Composer) obj, ((Integer) obj2).intValue());
                }
            });
        }
    }

    private static final List<UsbSerialPort> SuscTumbler$lambda$1(MutableState<List<UsbSerialPort>> mutableState) {
        return (List) ((State) mutableState).getValue();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final UsbSerialPort SuscTumbler$lambda$4(MutableState<UsbSerialPort> mutableState) {
        return (UsbSerialPort) ((State) mutableState).getValue();
    }

    private static final boolean SuscTumbler$lambda$7(MutableState<Boolean> mutableState) {
        return ((Boolean) ((State) mutableState).getValue()).booleanValue();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final void SuscTumbler$lambda$8(MutableState<Boolean> mutableState, boolean z) {
        mutableState.setValue(Boolean.valueOf(z));
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final boolean SuscTumbler$lambda$10(MutableState<Boolean> mutableState) {
        return ((Boolean) ((State) mutableState).getValue()).booleanValue();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final void SuscTumbler$lambda$11(MutableState<Boolean> mutableState, boolean z) {
        mutableState.setValue(Boolean.valueOf(z));
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* JADX WARN: Removed duplicated region for block: B:21:0x006d  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0014  */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:26:0x0082 -> B:27:0x0084). Please report as a decompilation issue!!! */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
        To view partially-correct code enable 'Show inconsistent code' option in preferences
    */
    public static final java.lang.Object SuscTumbler$sendAndWait(ru.cyclone.susc_tumbler.UsbSerialManager r8, byte[] r9, long r10, kotlin.coroutines.Continuation<? super byte[]> r12) {
        /*
            boolean r0 = r12 instanceof ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$sendAndWait$1
            if (r0 == 0) goto L14
            r0 = r12
            ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$sendAndWait$1 r0 = (ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$sendAndWait$1) r0
            int r1 = r0.label
            r2 = -2147483648(0xffffffff80000000, float:-0.0)
            r1 = r1 & r2
            if (r1 == 0) goto L14
            int r12 = r0.label
            int r12 = r12 - r2
            r0.label = r12
            goto L19
        L14:
            ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$sendAndWait$1 r0 = new ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$sendAndWait$1
            r0.<init>(r12)
        L19:
            java.lang.Object r12 = r0.result
            java.lang.Object r1 = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED()
            int r2 = r0.label
            r3 = 1
            if (r2 == 0) goto L3a
            if (r2 != r3) goto L32
            long r8 = r0.J$1
            long r10 = r0.J$0
            java.lang.Object r2 = r0.L$0
            ru.cyclone.susc_tumbler.UsbSerialManager r2 = (ru.cyclone.susc_tumbler.UsbSerialManager) r2
            kotlin.ResultKt.throwOnFailure(r12)
            goto L84
        L32:
            java.lang.IllegalStateException r8 = new java.lang.IllegalStateException
            java.lang.String r9 = "call to 'resume' before 'invoke' with coroutine"
            r8.<init>(r9)
            throw r8
        L3a:
            kotlin.ResultKt.throwOnFailure(r12)
            if (r9 != 0) goto L41
            r8 = 0
            return r8
        L41:
            r8.resetReceivedData()
            ru.cyclone.susc_tumbler.DebugLogger r12 = ru.cyclone.susc_tumbler.DebugLogger.INSTANCE
            java.lang.String r2 = ru.cyclone.susc_tumbler.UsbSerialManagerKt.toHexString(r9)
            java.lang.StringBuilder r4 = new java.lang.StringBuilder
            java.lang.String r5 = "Sent: "
            r4.<init>(r5)
            java.lang.StringBuilder r2 = r4.append(r2)
            java.lang.String r2 = r2.toString()
            java.lang.String r4 = "SUSC_TUMBLER"
            r12.i(r4, r2)
            r8.write(r9)
            r4 = 0
        L63:
            kotlinx.coroutines.flow.StateFlow r9 = r8.getReceivedDataFlow()
            java.lang.Object r9 = r9.getValue()
            if (r9 != 0) goto L8a
            int r9 = (r4 > r10 ? 1 : (r4 == r10 ? 0 : -1))
            if (r9 >= 0) goto L8a
            r0.L$0 = r8
            r0.J$0 = r10
            r0.J$1 = r4
            r0.label = r3
            r6 = 100
            java.lang.Object r9 = kotlinx.coroutines.DelayKt.delay(r6, r0)
            if (r9 != r1) goto L82
            return r1
        L82:
            r2 = r8
            r8 = r4
        L84:
            r12 = 100
            long r4 = (long) r12
            long r4 = r4 + r8
            r8 = r2
            goto L63
        L8a:
            kotlinx.coroutines.flow.StateFlow r8 = r8.getReceivedDataFlow()
            java.lang.Object r8 = r8.getValue()
            return r8
        */
        throw new UnsupportedOperationException("Method not decompiled: ru.cyclone.susc_tumbler.MainActivityKt.SuscTumbler$sendAndWait(ru.cyclone.susc_tumbler.UsbSerialManager, byte[], long, kotlin.coroutines.Continuation):java.lang.Object");
    }

    static /* synthetic */ Object SuscTumbler$sendAndWait$default(UsbSerialManager usbSerialManager, byte[] bArr, long j, Continuation continuation, int i, Object obj) {
        if ((i & 4) != 0) {
            j = CHECK_TIMEOUT;
        }
        return SuscTumbler$sendAndWait(usbSerialManager, bArr, j, continuation);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final Object SuscTumbler$performInitialization(UsbSerialManager usbSerialManager, Continuation<? super Unit> continuation) {
        Object objSuscTumbler$sendAndWait = SuscTumbler$sendAndWait(usbSerialManager, CommandBuilder.buildCommand$default(CommandBuilder.INSTANCE, "SS_RATE", 0, false, 4, null), INITIALIZATION_TIMEOUT, continuation);
        return objSuscTumbler$sendAndWait == IntrinsicsKt.getCOROUTINE_SUSPENDED() ? objSuscTumbler$sendAndWait : Unit.INSTANCE;
    }

    private static final void SuscTumbler$connectPort(Context context, UsbSerialManager usbSerialManager, MutableState<UsbSerialPort> mutableState, UsbSerialPort usbSerialPort) {
        Object systemService = context.getSystemService("usb");
        Intrinsics.checkNotNull(systemService, "null cannot be cast to non-null type android.hardware.usb.UsbManager");
        UsbManager usbManager = (UsbManager) systemService;
        if (!usbManager.hasPermission(usbSerialPort.getDriver().getDevice())) {
            usbManager.requestPermission(usbSerialPort.getDriver().getDevice(), PendingIntent.getBroadcast(context, 0, new Intent(ACTION_USB_PERMISSION_RESPONSE), AccessibilityEventCompat.TYPE_VIEW_TARGETED_BY_SCROLL));
        } else {
            mutableState.setValue(usbSerialPort);
            usbSerialManager.connect(usbSerialPort);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final void SuscTumbler$refreshDeviceList(Context context, UsbSerialManager usbSerialManager, MutableState<List<UsbSerialPort>> mutableState, MutableState<Boolean> mutableState2, MutableState<UsbSerialPort> mutableState3) {
        DebugLogger.INSTANCE.i(MAIN_LOG_TAG, "Refreshing devise list started.");
        Object systemService = context.getSystemService("usb");
        Intrinsics.checkNotNull(systemService, "null cannot be cast to non-null type android.hardware.usb.UsbManager");
        List<UsbSerialDriver> listFindAllDrivers = UsbSerialProber.getDefaultProber().findAllDrivers((UsbManager) systemService);
        Intrinsics.checkNotNullExpressionValue(listFindAllDrivers, "findAllDrivers(...)");
        ArrayList arrayList = new ArrayList();
        Iterator<T> it = listFindAllDrivers.iterator();
        while (it.hasNext()) {
            List<UsbSerialPort> ports = ((UsbSerialDriver) it.next()).getPorts();
            Intrinsics.checkNotNullExpressionValue(ports, "getPorts(...)");
            CollectionsKt.addAll(arrayList, ports);
        }
        mutableState.setValue(arrayList);
        if (SuscTumbler$lambda$1(mutableState).size() > 1 && !usbSerialManager.isConnected()) {
            SuscTumbler$lambda$8(mutableState2, true);
        } else {
            if (SuscTumbler$lambda$1(mutableState).isEmpty()) {
                return;
            }
            SuscTumbler$connectPort(context, usbSerialManager, mutableState3, SuscTumbler$lambda$1(mutableState).get(0));
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final DisposableEffectResult SuscTumbler$lambda$21$lambda$20(final Context context, UsbSerialManager usbSerialManager, MutableState mutableState, MutableState mutableState2, MutableState mutableState3, DisposableEffectScope DisposableEffect) {
        Intrinsics.checkNotNullParameter(DisposableEffect, "$this$DisposableEffect");
        final MainActivityKt$SuscTumbler$4$1$usbReceiver$1 mainActivityKt$SuscTumbler$4$1$usbReceiver$1 = new MainActivityKt$SuscTumbler$4$1$usbReceiver$1(usbSerialManager, mutableState, context, mutableState2, mutableState3);
        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction(ACTION_USB_PERMISSION_RESPONSE);
        intentFilter.addAction("android.hardware.usb.action.USB_DEVICE_ATTACHED");
        intentFilter.addAction("android.hardware.usb.action.USB_DEVICE_DETACHED");
        if (Build.VERSION.SDK_INT >= 33) {
            context.registerReceiver(mainActivityKt$SuscTumbler$4$1$usbReceiver$1, intentFilter, 4);
        } else {
            ContextCompat.registerReceiver(context, mainActivityKt$SuscTumbler$4$1$usbReceiver$1, intentFilter, 4);
        }
        return new DisposableEffectResult() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$lambda$21$lambda$20$$inlined$onDispose$1
            public void dispose() {
                context.unregisterReceiver(mainActivityKt$SuscTumbler$4$1$usbReceiver$1);
            }
        };
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final Unit SuscTumbler$lambda$23$lambda$22(MutableState mutableState, Context context, UsbSerialManager usbSerialManager, MutableState mutableState2, UsbSerialPort port) {
        Intrinsics.checkNotNullParameter(port, "port");
        SuscTumbler$lambda$8(mutableState, false);
        SuscTumbler$connectPort(context, usbSerialManager, mutableState2, port);
        return Unit.INSTANCE;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final Unit SuscTumbler$lambda$25$lambda$24(MutableState mutableState) {
        SuscTumbler$lambda$8(mutableState, false);
        return Unit.INSTANCE;
    }

    /* JADX INFO: renamed from: ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$8, reason: invalid class name */
    /* JADX INFO: compiled from: MainActivity.kt */
    @Metadata(k = 3, mv = {2, 0, 0}, xi = 48)
    static final class AnonymousClass8 implements Function3<PaddingValues, Composer, Integer, Unit> {
        final /* synthetic */ MutableState<UsbSerialPort> $connectedPort$delegate;
        final /* synthetic */ MutableState<Boolean> $isDevicePowerOn$delegate;
        final /* synthetic */ State<byte[]> $receivedData$delegate;
        final /* synthetic */ CoroutineScope $scope;
        final /* synthetic */ SnackbarHostState $snackbarHostState;
        final /* synthetic */ UsbSerialManager $usbSerialManager;

        AnonymousClass8(UsbSerialManager usbSerialManager, CoroutineScope coroutineScope, MutableState<UsbSerialPort> mutableState, MutableState<Boolean> mutableState2, State<byte[]> state, SnackbarHostState snackbarHostState) {
            this.$usbSerialManager = usbSerialManager;
            this.$scope = coroutineScope;
            this.$connectedPort$delegate = mutableState;
            this.$isDevicePowerOn$delegate = mutableState2;
            this.$receivedData$delegate = state;
            this.$snackbarHostState = snackbarHostState;
        }

        @Override // kotlin.jvm.functions.Function3
        public /* bridge */ /* synthetic */ Unit invoke(PaddingValues paddingValues, Composer composer, Integer num) {
            invoke(paddingValues, composer, num.intValue());
            return Unit.INSTANCE;
        }

        public final void invoke(PaddingValues innerPadding, Composer composer, int i) {
            int i2;
            Intrinsics.checkNotNullParameter(innerPadding, "innerPadding");
            ComposerKt.sourceInformation(composer, "C280@11288L2458:MainActivity.kt#6o5wwo");
            if ((i & 6) == 0) {
                i2 = i | (composer.changed(innerPadding) ? 4 : 2);
            } else {
                i2 = i;
            }
            if ((i2 & 19) != 18 || !composer.getSkipping()) {
                if (ComposerKt.isTraceInProgress()) {
                    ComposerKt.traceEventStart(45429054, i2, -1, "ru.cyclone.susc_tumbler.SuscTumbler.<anonymous> (MainActivity.kt:280)");
                }
                Modifier modifierNavigationBarsPadding = WindowInsetsPadding_androidKt.navigationBarsPadding(PaddingKt.padding(SizeKt.fillMaxSize$default(Modifier.Companion, 0.0f, 1, (Object) null), innerPadding));
                final UsbSerialManager usbSerialManager = this.$usbSerialManager;
                final CoroutineScope coroutineScope = this.$scope;
                MutableState<UsbSerialPort> mutableState = this.$connectedPort$delegate;
                MutableState<Boolean> mutableState2 = this.$isDevicePowerOn$delegate;
                State<byte[]> state = this.$receivedData$delegate;
                final SnackbarHostState snackbarHostState = this.$snackbarHostState;
                ComposerKt.sourceInformationMarkerStart(composer, -483455358, "CC(Column)P(2,3,1)85@4251L61,86@4317L133:Column.kt#2w3rfo");
                MeasurePolicy measurePolicyColumnMeasurePolicy = ColumnKt.columnMeasurePolicy(Arrangement.INSTANCE.getTop(), Alignment.Companion.getStart(), composer, 0);
                ComposerKt.sourceInformationMarkerStart(composer, -1323940314, "CC(Layout)P(!1,2)78@3182L23,81@3333L411:Layout.kt#80mrfh");
                int currentCompositeKeyHash = ComposablesKt.getCurrentCompositeKeyHash(composer, 0);
                CompositionLocalMap currentCompositionLocalMap = composer.getCurrentCompositionLocalMap();
                Modifier modifierMaterializeModifier = ComposedModifierKt.materializeModifier(composer, modifierNavigationBarsPadding);
                Function0 constructor = ComposeUiNode.Companion.getConstructor();
                ComposerKt.sourceInformationMarkerStart(composer, -692256719, "CC(ReusableComposeNode)P(1,2)376@14062L9:Composables.kt#9igjgp");
                if (!(composer.getApplier() instanceof Applier)) {
                    ComposablesKt.invalidApplier();
                }
                composer.startReusableNode();
                if (composer.getInserting()) {
                    composer.createNode(constructor);
                } else {
                    composer.useNode();
                }
                Composer composer2 = Updater.constructor-impl(composer);
                Updater.set-impl(composer2, measurePolicyColumnMeasurePolicy, ComposeUiNode.Companion.getSetMeasurePolicy());
                Updater.set-impl(composer2, currentCompositionLocalMap, ComposeUiNode.Companion.getSetResolvedCompositionLocals());
                Function2 setCompositeKeyHash = ComposeUiNode.Companion.getSetCompositeKeyHash();
                if (composer2.getInserting() || !Intrinsics.areEqual(composer2.rememberedValue(), Integer.valueOf(currentCompositeKeyHash))) {
                    composer2.updateRememberedValue(Integer.valueOf(currentCompositeKeyHash));
                    composer2.apply(Integer.valueOf(currentCompositeKeyHash), setCompositeKeyHash);
                }
                Updater.set-impl(composer2, modifierMaterializeModifier, ComposeUiNode.Companion.getSetModifier());
                ComposerKt.sourceInformationMarkerStart(composer, -384862393, "C87@4365L9:Column.kt#2w3rfo");
                ColumnScope columnScope = ColumnScopeInstance.INSTANCE;
                ComposerKt.sourceInformationMarkerStart(composer, -770006343, "C290@11719L311,297@12065L578,309@12676L326,316@13037L323,286@11463L2008:MainActivity.kt#6o5wwo");
                boolean z = MainActivityKt.SuscTumbler$lambda$4(mutableState) != null;
                boolean zSuscTumbler$lambda$10 = MainActivityKt.SuscTumbler$lambda$10(mutableState2);
                byte[] bArrSuscTumbler$lambda$13 = MainActivityKt.SuscTumbler$lambda$13(state);
                Pair<String, Integer> response = bArrSuscTumbler$lambda$13 != null ? CommandBuilder.INSTANCE.parseResponse(bArrSuscTumbler$lambda$13) : null;
                composer.startReplaceGroup(390809312);
                ComposerKt.sourceInformation(composer, "CC(remember):MainActivity.kt#9igjgp");
                boolean zChangedInstance = composer.changedInstance(usbSerialManager);
                Object objRememberedValue = composer.rememberedValue();
                if (zChangedInstance || objRememberedValue == Composer.Companion.getEmpty()) {
                    objRememberedValue = new Function1() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$8$$ExternalSyntheticLambda0
                        @Override // kotlin.jvm.functions.Function1
                        public final Object invoke(Object obj) {
                            return MainActivityKt.AnonymousClass8.invoke$lambda$13$lambda$3$lambda$2(usbSerialManager, ((Integer) obj).intValue());
                        }
                    };
                    composer.updateRememberedValue(objRememberedValue);
                }
                Function1 function1 = (Function1) objRememberedValue;
                composer.endReplaceGroup();
                composer.startReplaceGroup(390820651);
                ComposerKt.sourceInformation(composer, "CC(remember):MainActivity.kt#9igjgp");
                boolean zChangedInstance2 = composer.changedInstance(usbSerialManager) | composer.changedInstance(coroutineScope);
                Object objRememberedValue2 = composer.rememberedValue();
                if (zChangedInstance2 || objRememberedValue2 == Composer.Companion.getEmpty()) {
                    objRememberedValue2 = new Function0() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$8$$ExternalSyntheticLambda1
                        @Override // kotlin.jvm.functions.Function0
                        public final Object invoke() {
                            return MainActivityKt.AnonymousClass8.invoke$lambda$13$lambda$6$lambda$5(coroutineScope, usbSerialManager, snackbarHostState);
                        }
                    };
                    composer.updateRememberedValue(objRememberedValue2);
                }
                Function0 function0 = (Function0) objRememberedValue2;
                composer.endReplaceGroup();
                composer.startReplaceGroup(390839951);
                ComposerKt.sourceInformation(composer, "CC(remember):MainActivity.kt#9igjgp");
                boolean zChangedInstance3 = composer.changedInstance(usbSerialManager);
                Object objRememberedValue3 = composer.rememberedValue();
                if (zChangedInstance3 || objRememberedValue3 == Composer.Companion.getEmpty()) {
                    objRememberedValue3 = new Function1() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$8$$ExternalSyntheticLambda2
                        @Override // kotlin.jvm.functions.Function1
                        public final Object invoke(Object obj) {
                            return MainActivityKt.AnonymousClass8.invoke$lambda$13$lambda$9$lambda$8(usbSerialManager, ((Boolean) obj).booleanValue());
                        }
                    };
                    composer.updateRememberedValue(objRememberedValue3);
                }
                Function1 function12 = (Function1) objRememberedValue3;
                composer.endReplaceGroup();
                composer.startReplaceGroup(390851500);
                ComposerKt.sourceInformation(composer, "CC(remember):MainActivity.kt#9igjgp");
                boolean zChangedInstance4 = composer.changedInstance(usbSerialManager);
                Object objRememberedValue4 = composer.rememberedValue();
                if (zChangedInstance4 || objRememberedValue4 == Composer.Companion.getEmpty()) {
                    objRememberedValue4 = new Function1() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$8$$ExternalSyntheticLambda3
                        @Override // kotlin.jvm.functions.Function1
                        public final Object invoke(Object obj) {
                            return MainActivityKt.AnonymousClass8.invoke$lambda$13$lambda$12$lambda$11(usbSerialManager, ((Boolean) obj).booleanValue());
                        }
                    };
                    composer.updateRememberedValue(objRememberedValue4);
                }
                composer.endReplaceGroup();
                MainActivityKt.SuscTumblerContent(z, zSuscTumbler$lambda$10, response, function1, function0, function12, (Function1) objRememberedValue4, SizeKt.wrapContentSize$default(ColumnScope.weight$default(columnScope, SizeKt.fillMaxWidth$default(Modifier.Companion, 0.0f, 1, (Object) null), 1.0f, false, 2, (Object) null), Alignment.Companion.getCenter(), false, 2, (Object) null), composer, 0, 0);
                composer.startReplaceGroup(390865733);
                ComposerKt.sourceInformation(composer, "326@13525L19,327@13573L149");
                composer.endReplaceGroup();
                ComposerKt.sourceInformationMarkerEnd(composer);
                ComposerKt.sourceInformationMarkerEnd(composer);
                composer.endNode();
                ComposerKt.sourceInformationMarkerEnd(composer);
                ComposerKt.sourceInformationMarkerEnd(composer);
                ComposerKt.sourceInformationMarkerEnd(composer);
                if (ComposerKt.isTraceInProgress()) {
                    ComposerKt.traceEventEnd();
                    return;
                }
                return;
            }
            composer.skipToGroupEnd();
        }

        /* JADX INFO: Access modifiers changed from: private */
        public static final Unit invoke$lambda$13$lambda$3$lambda$2(UsbSerialManager usbSerialManager, int i) {
            byte[] bArrBuildCommand = CommandBuilder.INSTANCE.buildCommand("SS_RATE", i, true);
            if (bArrBuildCommand != null) {
                DebugLogger.INSTANCE.i(MainActivityKt.MAIN_LOG_TAG, "Sent: " + UsbSerialManagerKt.toHexString(bArrBuildCommand));
                usbSerialManager.write(bArrBuildCommand);
            }
            return Unit.INSTANCE;
        }

        /* JADX INFO: Access modifiers changed from: private */
        public static final Unit invoke$lambda$13$lambda$6$lambda$5(CoroutineScope coroutineScope, UsbSerialManager usbSerialManager, SnackbarHostState snackbarHostState) {
            byte[] bArrBuildCommand = CommandBuilder.INSTANCE.buildCommand("START_CFG", 1, true);
            if (bArrBuildCommand == null) {
                BuildersKt__Builders_commonKt.launch$default(coroutineScope, null, null, new MainActivityKt$SuscTumbler$8$1$3$1$2(snackbarHostState, null), 3, null);
            } else {
                DebugLogger.INSTANCE.i(MainActivityKt.MAIN_LOG_TAG, "Sent: " + UsbSerialManagerKt.toHexString(bArrBuildCommand));
                usbSerialManager.write(bArrBuildCommand);
                BuildersKt__Builders_commonKt.launch$default(coroutineScope, null, null, new MainActivityKt$SuscTumbler$8$1$3$1$1$1(snackbarHostState, null), 3, null);
            }
            return Unit.INSTANCE;
        }

        /* JADX INFO: Access modifiers changed from: private */
        public static final Unit invoke$lambda$13$lambda$9$lambda$8(UsbSerialManager usbSerialManager, boolean z) {
            byte[] bArrBuildCommand = CommandBuilder.INSTANCE.buildCommand("USER_LED", z ? 1 : 0, true);
            if (bArrBuildCommand != null) {
                DebugLogger.INSTANCE.i(MainActivityKt.MAIN_LOG_TAG, "Sent: " + UsbSerialManagerKt.toHexString(bArrBuildCommand));
                usbSerialManager.write(bArrBuildCommand);
            }
            return Unit.INSTANCE;
        }

        /* JADX INFO: Access modifiers changed from: private */
        public static final Unit invoke$lambda$13$lambda$12$lambda$11(UsbSerialManager usbSerialManager, boolean z) {
            byte[] bArrBuildCommand = CommandBuilder.INSTANCE.buildCommand("RANGE", z ? 1 : 0, true);
            if (bArrBuildCommand != null) {
                DebugLogger.INSTANCE.i(MainActivityKt.MAIN_LOG_TAG, "Sent: " + UsbSerialManagerKt.toHexString(bArrBuildCommand));
                usbSerialManager.write(bArrBuildCommand);
            }
            return Unit.INSTANCE;
        }
    }

    public static final void PortSelectionDialog(final List<? extends UsbSerialPort> ports, final Function1<? super UsbSerialPort, Unit> onPortSelected, Function0<Unit> onDismiss, Composer composer, final int i) {
        int i2;
        final Function0<Unit> function0;
        Intrinsics.checkNotNullParameter(ports, "ports");
        Intrinsics.checkNotNullParameter(onPortSelected, "onPortSelected");
        Intrinsics.checkNotNullParameter(onDismiss, "onDismiss");
        Composer composerStartRestartGroup = composer.startRestartGroup(1009026114);
        ComposerKt.sourceInformation(composerStartRestartGroup, "C(PortSelectionDialog)P(2,1)351@14238L651,351@14201L688:MainActivity.kt#6o5wwo");
        if ((i & 6) == 0) {
            i2 = (composerStartRestartGroup.changedInstance(ports) ? 4 : 2) | i;
        } else {
            i2 = i;
        }
        if ((i & 48) == 0) {
            i2 |= composerStartRestartGroup.changedInstance(onPortSelected) ? 32 : 16;
        }
        if ((i & 384) == 0) {
            i2 |= composerStartRestartGroup.changedInstance(onDismiss) ? 256 : 128;
        }
        if ((i2 & 147) != 146 || !composerStartRestartGroup.getSkipping()) {
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventStart(1009026114, i2, -1, "ru.cyclone.susc_tumbler.PortSelectionDialog (MainActivity.kt:350)");
            }
            function0 = onDismiss;
            AndroidDialog_androidKt.Dialog(function0, (DialogProperties) null, ComposableLambdaKt.rememberComposableLambda(2080557963, true, new Function2<Composer, Integer, Unit>() { // from class: ru.cyclone.susc_tumbler.MainActivityKt.PortSelectionDialog.1

                /* JADX INFO: renamed from: ru.cyclone.susc_tumbler.MainActivityKt$PortSelectionDialog$1$1, reason: invalid class name and collision with other inner class name */
                /* JADX INFO: compiled from: MainActivity.kt */
                @Metadata(k = 3, mv = {2, 0, 0}, xi = 48)
                static final class C00081 implements Function3<ColumnScope, Composer, Integer, Unit> {
                    final /* synthetic */ Function1<UsbSerialPort, Unit> $onPortSelected;
                    final /* synthetic */ List<UsbSerialPort> $ports;

                    /* JADX WARN: Multi-variable type inference failed */
                    C00081(List<? extends UsbSerialPort> list, Function1<? super UsbSerialPort, Unit> function1) {
                        this.$ports = list;
                        this.$onPortSelected = function1;
                    }

                    @Override // kotlin.jvm.functions.Function3
                    public /* bridge */ /* synthetic */ Unit invoke(ColumnScope columnScope, Composer composer, Integer num) {
                        invoke(columnScope, composer, num.intValue());
                        return Unit.INSTANCE;
                    }

                    public final void invoke(ColumnScope Card, Composer composer, int i) {
                        Intrinsics.checkNotNullParameter(Card, "$this$Card");
                        ComposerKt.sourceInformation(composer, "C353@14267L606:MainActivity.kt#6o5wwo");
                        if ((i & 17) != 16 || !composer.getSkipping()) {
                            if (ComposerKt.isTraceInProgress()) {
                                ComposerKt.traceEventStart(-908412071, i, -1, "ru.cyclone.susc_tumbler.PortSelectionDialog.<anonymous>.<anonymous> (MainActivity.kt:353)");
                            }
                            float f = 16;
                            Modifier modifier = PaddingKt.padding-3ABfNKs(Modifier.Companion, Dp.constructor-impl(f));
                            List<UsbSerialPort> list = this.$ports;
                            final Function1<UsbSerialPort, Unit> function1 = this.$onPortSelected;
                            ComposerKt.sourceInformationMarkerStart(composer, -483455358, "CC(Column)P(2,3,1)85@4251L61,86@4317L133:Column.kt#2w3rfo");
                            MeasurePolicy measurePolicyColumnMeasurePolicy = ColumnKt.columnMeasurePolicy(Arrangement.INSTANCE.getTop(), Alignment.Companion.getStart(), composer, 0);
                            ComposerKt.sourceInformationMarkerStart(composer, -1323940314, "CC(Layout)P(!1,2)78@3182L23,81@3333L411:Layout.kt#80mrfh");
                            int currentCompositeKeyHash = ComposablesKt.getCurrentCompositeKeyHash(composer, 0);
                            CompositionLocalMap currentCompositionLocalMap = composer.getCurrentCompositionLocalMap();
                            Modifier modifierMaterializeModifier = ComposedModifierKt.materializeModifier(composer, modifier);
                            Function0 constructor = ComposeUiNode.Companion.getConstructor();
                            ComposerKt.sourceInformationMarkerStart(composer, -692256719, "CC(ReusableComposeNode)P(1,2)376@14062L9:Composables.kt#9igjgp");
                            if (!(composer.getApplier() instanceof Applier)) {
                                ComposablesKt.invalidApplier();
                            }
                            composer.startReusableNode();
                            if (composer.getInserting()) {
                                composer.createNode(constructor);
                            } else {
                                composer.useNode();
                            }
                            Composer composer2 = Updater.constructor-impl(composer);
                            Updater.set-impl(composer2, measurePolicyColumnMeasurePolicy, ComposeUiNode.Companion.getSetMeasurePolicy());
                            Updater.set-impl(composer2, currentCompositionLocalMap, ComposeUiNode.Companion.getSetResolvedCompositionLocals());
                            Function2 setCompositeKeyHash = ComposeUiNode.Companion.getSetCompositeKeyHash();
                            if (composer2.getInserting() || !Intrinsics.areEqual(composer2.rememberedValue(), Integer.valueOf(currentCompositeKeyHash))) {
                                composer2.updateRememberedValue(Integer.valueOf(currentCompositeKeyHash));
                                composer2.apply(Integer.valueOf(currentCompositeKeyHash), setCompositeKeyHash);
                            }
                            Updater.set-impl(composer2, modifierMaterializeModifier, ComposeUiNode.Companion.getSetModifier());
                            ComposerKt.sourceInformationMarkerStart(composer, -384862393, "C87@4365L9:Column.kt#2w3rfo");
                            ColumnScope columnScope = ColumnScopeInstance.INSTANCE;
                            ComposerKt.sourceInformationMarkerStart(composer, -406339706, "C354@14373L10,354@14328L67,355@14412L41:MainActivity.kt#6o5wwo");
                            TextKt.Text--4IGK_g("Выберите порт:", (Modifier) null, 0L, 0L, (FontStyle) null, (FontWeight) null, (FontFamily) null, 0L, (TextDecoration) null, (TextAlign) null, 0L, 0, false, 0, 0, (Function1) null, MaterialTheme.INSTANCE.getTypography(composer, MaterialTheme.$stable).getTitleLarge(), composer, 6, 0, 65534);
                            Composer composer3 = composer;
                            SpacerKt.Spacer(SizeKt.height-3ABfNKs(Modifier.Companion, Dp.constructor-impl(f)), composer3, 6);
                            composer3.startReplaceGroup(1649464841);
                            ComposerKt.sourceInformation(composer3, "*361@14741L24,357@14514L327");
                            for (final UsbSerialPort usbSerialPort : list) {
                                String str = "Порт #" + usbSerialPort.getPortNumber() + " (" + usbSerialPort.getDriver().getDevice().getDeviceName() + ")";
                                Modifier modifierFillMaxWidth$default = SizeKt.fillMaxWidth$default(Modifier.Companion, 0.0f, 1, (Object) null);
                                composer3.startReplaceGroup(-1043597119);
                                ComposerKt.sourceInformation(composer3, "CC(remember):MainActivity.kt#9igjgp");
                                boolean zChanged = composer3.changed(function1) | composer3.changedInstance(usbSerialPort);
                                Object objRememberedValue = composer3.rememberedValue();
                                if (zChanged || objRememberedValue == Composer.Companion.getEmpty()) {
                                    objRememberedValue = new Function0() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$PortSelectionDialog$1$1$$ExternalSyntheticLambda0
                                        @Override // kotlin.jvm.functions.Function0
                                        public final Object invoke() {
                                            return MainActivityKt.AnonymousClass1.C00081.invoke$lambda$3$lambda$2$lambda$1$lambda$0(function1, usbSerialPort);
                                        }
                                    };
                                    composer3.updateRememberedValue(objRememberedValue);
                                }
                                composer3.endReplaceGroup();
                                TextKt.Text--4IGK_g(str, PaddingKt.padding-VpY3zN4$default(ClickableKt.clickable-XHw0xAI$default(modifierFillMaxWidth$default, false, (String) null, (Role) null, (Function0) objRememberedValue, 7, (Object) null), 0.0f, Dp.constructor-impl(8), 1, (Object) null), 0L, 0L, (FontStyle) null, (FontWeight) null, (FontFamily) null, 0L, (TextDecoration) null, (TextAlign) null, 0L, 0, false, 0, 0, (Function1) null, (TextStyle) null, composer, 0, 0, 131068);
                                composer3 = composer;
                            }
                            composer.endReplaceGroup();
                            ComposerKt.sourceInformationMarkerEnd(composer);
                            ComposerKt.sourceInformationMarkerEnd(composer);
                            composer.endNode();
                            ComposerKt.sourceInformationMarkerEnd(composer);
                            ComposerKt.sourceInformationMarkerEnd(composer);
                            ComposerKt.sourceInformationMarkerEnd(composer);
                            if (ComposerKt.isTraceInProgress()) {
                                ComposerKt.traceEventEnd();
                                return;
                            }
                            return;
                        }
                        composer.skipToGroupEnd();
                    }

                    /* JADX INFO: Access modifiers changed from: private */
                    public static final Unit invoke$lambda$3$lambda$2$lambda$1$lambda$0(Function1 function1, UsbSerialPort usbSerialPort) {
                        function1.invoke(usbSerialPort);
                        return Unit.INSTANCE;
                    }
                }

                @Override // kotlin.jvm.functions.Function2
                public /* bridge */ /* synthetic */ Unit invoke(Composer composer2, Integer num) {
                    invoke(composer2, num.intValue());
                    return Unit.INSTANCE;
                }

                public final void invoke(Composer composer2, int i3) {
                    ComposerKt.sourceInformation(composer2, "C352@14253L630,352@14248L635:MainActivity.kt#6o5wwo");
                    if ((i3 & 3) != 2 || !composer2.getSkipping()) {
                        if (ComposerKt.isTraceInProgress()) {
                            ComposerKt.traceEventStart(2080557963, i3, -1, "ru.cyclone.susc_tumbler.PortSelectionDialog.<anonymous> (MainActivity.kt:352)");
                        }
                        CardKt.Card((Modifier) null, (Shape) null, (CardColors) null, (CardElevation) null, (BorderStroke) null, ComposableLambdaKt.rememberComposableLambda(-908412071, true, new C00081(ports, onPortSelected), composer2, 54), composer2, ProfileVerifier.CompilationStatus.RESULT_CODE_ERROR_CANT_WRITE_PROFILE_VERIFICATION_RESULT_CACHE_FILE, 31);
                        if (ComposerKt.isTraceInProgress()) {
                            ComposerKt.traceEventEnd();
                            return;
                        }
                        return;
                    }
                    composer2.skipToGroupEnd();
                }
            }, composerStartRestartGroup, 54), composerStartRestartGroup, ((i2 >> 6) & 14) | 384, 2);
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventEnd();
            }
        } else {
            composerStartRestartGroup.skipToGroupEnd();
            function0 = onDismiss;
        }
        ScopeUpdateScope scopeUpdateScopeEndRestartGroup = composerStartRestartGroup.endRestartGroup();
        if (scopeUpdateScopeEndRestartGroup != null) {
            scopeUpdateScopeEndRestartGroup.updateScope(new Function2() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$$ExternalSyntheticLambda4
                @Override // kotlin.jvm.functions.Function2
                public final Object invoke(Object obj, Object obj2) {
                    return MainActivityKt.PortSelectionDialog$lambda$28(ports, onPortSelected, function0, i, (Composer) obj, ((Integer) obj2).intValue());
                }
            });
        }
    }

    public static final void SuscTumblerContent(final boolean z, final boolean z2, final Pair<String, Integer> pair, final Function1<? super Integer, Unit> onChangeRequest, final Function0<Unit> onWriteRequest, final Function1<? super Boolean, Unit> onLEDRequest, final Function1<? super Boolean, Unit> onRangeRequest, Modifier modifier, Composer composer, final int i, final int i2) {
        int i3;
        final Modifier modifier2;
        char c;
        final MutableFloatState mutableFloatState;
        int i4;
        char c2;
        float f;
        Pair<String, Integer> pair2;
        String strValueOf;
        Composer composer2;
        String strValueOf2;
        Intrinsics.checkNotNullParameter(onChangeRequest, "onChangeRequest");
        Intrinsics.checkNotNullParameter(onWriteRequest, "onWriteRequest");
        Intrinsics.checkNotNullParameter(onLEDRequest, "onLEDRequest");
        Intrinsics.checkNotNullParameter(onRangeRequest, "onRangeRequest");
        Composer composerStartRestartGroup = composer.startRestartGroup(662813508);
        ComposerKt.sourceInformation(composerStartRestartGroup, "C(SuscTumblerContent)P(!3,4,7,5,6)393@15772L5427:MainActivity.kt#6o5wwo");
        if ((i2 & 1) != 0) {
            i3 = i | 6;
        } else if ((i & 6) == 0) {
            i3 = (composerStartRestartGroup.changed(z) ? 4 : 2) | i;
        } else {
            i3 = i;
        }
        if ((i2 & 2) != 0) {
            i3 |= 48;
        } else if ((i & 48) == 0) {
            i3 |= composerStartRestartGroup.changed(z2) ? 32 : 16;
        }
        if ((i2 & 4) != 0) {
            i3 |= 384;
        } else if ((i & 384) == 0) {
            i3 |= composerStartRestartGroup.changed(pair) ? 256 : 128;
        }
        if ((i2 & 8) != 0) {
            i3 |= 3072;
        } else if ((i & 3072) == 0) {
            i3 |= composerStartRestartGroup.changedInstance(onChangeRequest) ? 2048 : 1024;
        }
        if ((i2 & 16) != 0) {
            i3 |= 24576;
        } else if ((i & 24576) == 0) {
            i3 |= composerStartRestartGroup.changedInstance(onWriteRequest) ? 16384 : 8192;
        }
        if ((i2 & 32) != 0) {
            i3 |= ProfileVerifier.CompilationStatus.RESULT_CODE_ERROR_CANT_WRITE_PROFILE_VERIFICATION_RESULT_CACHE_FILE;
        } else if ((i & ProfileVerifier.CompilationStatus.RESULT_CODE_ERROR_CANT_WRITE_PROFILE_VERIFICATION_RESULT_CACHE_FILE) == 0) {
            i3 |= composerStartRestartGroup.changedInstance(onLEDRequest) ? 131072 : 65536;
        }
        if ((i2 & 64) != 0) {
            i3 |= 1572864;
        } else if ((i & 1572864) == 0) {
            i3 |= composerStartRestartGroup.changedInstance(onRangeRequest) ? 1048576 : 524288;
        }
        int i5 = i2 & 128;
        if (i5 != 0) {
            i3 |= 12582912;
            modifier2 = modifier;
        } else {
            modifier2 = modifier;
            if ((i & 12582912) == 0) {
                i3 |= composerStartRestartGroup.changed(modifier2) ? 8388608 : 4194304;
            }
        }
        if ((i3 & 4793491) != 4793490 || !composerStartRestartGroup.getSkipping()) {
            Modifier modifier3 = i5 != 0 ? (Modifier) Modifier.Companion : modifier2;
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventStart(662813508, i3, -1, "ru.cyclone.susc_tumbler.SuscTumblerContent (MainActivity.kt:392)");
            }
            float f2 = 16;
            Modifier modifier4 = PaddingKt.padding-3ABfNKs(modifier3, Dp.constructor-impl(f2));
            Alignment.Horizontal centerHorizontally = Alignment.Companion.getCenterHorizontally();
            Arrangement.Vertical center = Arrangement.INSTANCE.getCenter();
            ComposerKt.sourceInformationMarkerStart(composerStartRestartGroup, -483455358, "CC(Column)P(2,3,1)85@4251L61,86@4317L133:Column.kt#2w3rfo");
            MeasurePolicy measurePolicyColumnMeasurePolicy = ColumnKt.columnMeasurePolicy(center, centerHorizontally, composerStartRestartGroup, 54);
            ComposerKt.sourceInformationMarkerStart(composerStartRestartGroup, -1323940314, "CC(Layout)P(!1,2)78@3182L23,81@3333L411:Layout.kt#80mrfh");
            int currentCompositeKeyHash = ComposablesKt.getCurrentCompositeKeyHash(composerStartRestartGroup, 0);
            CompositionLocalMap currentCompositionLocalMap = composerStartRestartGroup.getCurrentCompositionLocalMap();
            Modifier modifierMaterializeModifier = ComposedModifierKt.materializeModifier(composerStartRestartGroup, modifier4);
            Function0 constructor = ComposeUiNode.Companion.getConstructor();
            ComposerKt.sourceInformationMarkerStart(composerStartRestartGroup, -692256719, "CC(ReusableComposeNode)P(1,2)376@14062L9:Composables.kt#9igjgp");
            if (!(composerStartRestartGroup.getApplier() instanceof Applier)) {
                ComposablesKt.invalidApplier();
            }
            composerStartRestartGroup.startReusableNode();
            if (composerStartRestartGroup.getInserting()) {
                composerStartRestartGroup.createNode(constructor);
            } else {
                composerStartRestartGroup.useNode();
            }
            Composer composer3 = Updater.constructor-impl(composerStartRestartGroup);
            Updater.set-impl(composer3, measurePolicyColumnMeasurePolicy, ComposeUiNode.Companion.getSetMeasurePolicy());
            Updater.set-impl(composer3, currentCompositionLocalMap, ComposeUiNode.Companion.getSetResolvedCompositionLocals());
            Function2 setCompositeKeyHash = ComposeUiNode.Companion.getSetCompositeKeyHash();
            if (composer3.getInserting() || !Intrinsics.areEqual(composer3.rememberedValue(), Integer.valueOf(currentCompositeKeyHash))) {
                composer3.updateRememberedValue(Integer.valueOf(currentCompositeKeyHash));
                composer3.apply(Integer.valueOf(currentCompositeKeyHash), setCompositeKeyHash);
            }
            Updater.set-impl(composer3, modifierMaterializeModifier, ComposeUiNode.Companion.getSetModifier());
            ComposerKt.sourceInformationMarkerStart(composerStartRestartGroup, -384862393, "C87@4365L9:Column.kt#2w3rfo");
            ColumnScope columnScope = ColumnScopeInstance.INSTANCE;
            ComposerKt.sourceInformationMarkerStart(composerStartRestartGroup, 1553606298, "C:MainActivity.kt#6o5wwo");
            if (!z) {
                modifier2 = modifier3;
                composerStartRestartGroup.startReplaceGroup(1558378623);
                ComposerKt.sourceInformation(composerStartRestartGroup, "505@20962L83,507@21134L35,504@20929L254");
                ImageKt.Image(PainterResources_androidKt.painterResource(R.drawable.link_off_200dp_434343_fill0_wght500_grad200_opsz48, composerStartRestartGroup, 0), StringResources_androidKt.stringResource(R.string.disconnect, composerStartRestartGroup, 0), SizeKt.size-3ABfNKs(Modifier.Companion, Dp.constructor-impl(150)), (Alignment) null, (ContentScale) null, 0.0f, (ColorFilter) null, composerStartRestartGroup, 384, 120);
                composerStartRestartGroup = composerStartRestartGroup;
                composerStartRestartGroup.endReplaceGroup();
            } else {
                composerStartRestartGroup.startReplaceGroup(1553619596);
                ComposerKt.sourceInformation(composerStartRestartGroup, "399@16002L34,400@16065L34,401@16134L36,402@16217L622,402@16183L656");
                composerStartRestartGroup.startReplaceGroup(1019944143);
                ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
                Object objRememberedValue = composerStartRestartGroup.rememberedValue();
                if (objRememberedValue == Composer.Companion.getEmpty()) {
                    objRememberedValue = SnapshotStateKt.mutableStateOf$default(false, (SnapshotMutationPolicy) null, 2, (Object) null);
                    composerStartRestartGroup.updateRememberedValue(objRememberedValue);
                }
                MutableState mutableState = (MutableState) objRememberedValue;
                composerStartRestartGroup.endReplaceGroup();
                composerStartRestartGroup.startReplaceGroup(1019946159);
                ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
                Object objRememberedValue2 = composerStartRestartGroup.rememberedValue();
                if (objRememberedValue2 == Composer.Companion.getEmpty()) {
                    c = 2;
                    objRememberedValue2 = SnapshotStateKt.mutableStateOf$default(false, (SnapshotMutationPolicy) null, 2, (Object) null);
                    composerStartRestartGroup.updateRememberedValue(objRememberedValue2);
                } else {
                    c = 2;
                }
                MutableState mutableState2 = (MutableState) objRememberedValue2;
                composerStartRestartGroup.endReplaceGroup();
                composerStartRestartGroup.startReplaceGroup(1019948369);
                ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
                Object objRememberedValue3 = composerStartRestartGroup.rememberedValue();
                Modifier modifier5 = modifier3;
                if (objRememberedValue3 == Composer.Companion.getEmpty()) {
                    objRememberedValue3 = PrimitiveSnapshotStateKt.mutableFloatStateOf(5.0f);
                    composerStartRestartGroup.updateRememberedValue(objRememberedValue3);
                }
                MutableFloatState mutableFloatState2 = (MutableFloatState) objRememberedValue3;
                composerStartRestartGroup.endReplaceGroup();
                composerStartRestartGroup.startReplaceGroup(1019951611);
                ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
                boolean z3 = (i3 & 896) == 256;
                MainActivityKt$SuscTumblerContent$1$1$1 mainActivityKt$SuscTumblerContent$1$1$1RememberedValue = composerStartRestartGroup.rememberedValue();
                if (z3 || mainActivityKt$SuscTumblerContent$1$1$1RememberedValue == Composer.Companion.getEmpty()) {
                    char c3 = c;
                    mutableFloatState = mutableFloatState2;
                    i4 = i3;
                    c2 = c3;
                    f = f2;
                    pair2 = pair;
                    mainActivityKt$SuscTumblerContent$1$1$1RememberedValue = new MainActivityKt$SuscTumblerContent$1$1$1(pair, mutableState, mutableFloatState, mutableState2, null);
                    composerStartRestartGroup.updateRememberedValue(mainActivityKt$SuscTumblerContent$1$1$1RememberedValue);
                } else {
                    i4 = i3;
                    c2 = c;
                    f = f2;
                    mutableFloatState = mutableFloatState2;
                    pair2 = pair;
                }
                composerStartRestartGroup.endReplaceGroup();
                EffectsKt.LaunchedEffect(pair2, (Function2) mainActivityKt$SuscTumblerContent$1$1$1RememberedValue, composerStartRestartGroup, (i4 >> 6) & 14);
                if (z2) {
                    composerStartRestartGroup.startReplaceGroup(1554469523);
                    ComposerKt.sourceInformation(composerStartRestartGroup, "453@18673L27,488@20209L41,489@20284L20,489@20267L114");
                    composerStartRestartGroup.startReplaceGroup(1019974260);
                    ComposerKt.sourceInformation(composerStartRestartGroup, "420@16986L1590,420@16936L1640");
                    composerStartRestartGroup.endReplaceGroup();
                    modifier2 = modifier5;
                    TextKt.Text--4IGK_g("Полоса: " + (SuscTumblerContent$lambda$45$lambda$33(mutableState2) ? "500" : "812,5") + " КГц", (Modifier) null, 0L, 0L, (FontStyle) null, (FontWeight) null, (FontFamily) null, 0L, (TextDecoration) null, (TextAlign) null, 0L, 0, false, 0, 0, (Function1) null, (TextStyle) null, composerStartRestartGroup, 0, 0, 131070);
                    if (SuscTumblerContent$lambda$45$lambda$33(mutableState2)) {
                        composerStartRestartGroup.startReplaceGroup(1556225332);
                        ComposerKt.sourceInformation(composerStartRestartGroup, "459@18932L20,462@19069L143,460@18973L445");
                        if (SuscTumblerContent$lambda$45$lambda$36(mutableFloatState) == 5.0f) {
                            strValueOf2 = "микс 8 и 9";
                        } else {
                            strValueOf2 = String.valueOf(SuscTumblerContent$lambda$45$lambda$36(mutableFloatState));
                        }
                        TextKt.Text--4IGK_g("КРС: " + strValueOf2, (Modifier) null, 0L, 0L, (FontStyle) null, (FontWeight) null, (FontFamily) null, 0L, (TextDecoration) null, (TextAlign) null, 0L, 0, false, 0, 0, (Function1) null, (TextStyle) null, composerStartRestartGroup, 0, 0, 131070);
                        float fSuscTumblerContent$lambda$45$lambda$36 = SuscTumblerContent$lambda$45$lambda$36(mutableFloatState);
                        ClosedFloatingPointRange<Float> closedFloatingPointRangeRangeTo = RangesKt.rangeTo(5.0f, 10.0f);
                        Modifier modifier6 = PaddingKt.padding-VpY3zN4$default(Modifier.Companion, Dp.constructor-impl(f), 0.0f, 2, (Object) null);
                        composerStartRestartGroup.startReplaceGroup(1020042396);
                        ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
                        boolean z4 = (i4 & 7168) == 2048;
                        Object objRememberedValue4 = composerStartRestartGroup.rememberedValue();
                        if (z4 || objRememberedValue4 == Composer.Companion.getEmpty()) {
                            objRememberedValue4 = new Function1() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$$ExternalSyntheticLambda6
                                @Override // kotlin.jvm.functions.Function1
                                public final Object invoke(Object obj) {
                                    return MainActivityKt.SuscTumblerContent$lambda$45$lambda$40$lambda$39(onChangeRequest, mutableFloatState, ((Float) obj).floatValue());
                                }
                            };
                            composerStartRestartGroup.updateRememberedValue(objRememberedValue4);
                        }
                        composerStartRestartGroup.endReplaceGroup();
                        SliderKt.Slider(fSuscTumblerContent$lambda$45$lambda$36, (Function1) objRememberedValue4, modifier6, false, closedFloatingPointRangeRangeTo, 4, (Function0) null, (SliderColors) null, (MutableInteractionSource) null, composerStartRestartGroup, 196992, 456);
                        composer2 = composerStartRestartGroup;
                        composer2.endReplaceGroup();
                    } else {
                        composerStartRestartGroup.startReplaceGroup(1556932039);
                        ComposerKt.sourceInformation(composerStartRestartGroup, "476@19687L20,479@19824L143,477@19728L446");
                        float fSuscTumblerContent$lambda$45$lambda$362 = SuscTumblerContent$lambda$45$lambda$36(mutableFloatState);
                        if (fSuscTumblerContent$lambda$45$lambda$362 == 3.0f) {
                            strValueOf = "микс 7 и 8";
                        } else if (fSuscTumblerContent$lambda$45$lambda$362 == 4.0f) {
                            strValueOf = "микс 9 и 10";
                        } else {
                            strValueOf = String.valueOf(SuscTumblerContent$lambda$45$lambda$36(mutableFloatState));
                        }
                        TextKt.Text--4IGK_g("КРС: " + strValueOf, (Modifier) null, 0L, 0L, (FontStyle) null, (FontWeight) null, (FontFamily) null, 0L, (TextDecoration) null, (TextAlign) null, 0L, 0, false, 0, 0, (Function1) null, (TextStyle) null, composerStartRestartGroup, 0, 0, 131070);
                        float fSuscTumblerContent$lambda$45$lambda$363 = SuscTumblerContent$lambda$45$lambda$36(mutableFloatState);
                        ClosedFloatingPointRange<Float> closedFloatingPointRangeRangeTo2 = RangesKt.rangeTo(3.0f, 11.0f);
                        Modifier modifier7 = PaddingKt.padding-VpY3zN4$default(Modifier.Companion, Dp.constructor-impl(f), 0.0f, 2, (Object) null);
                        composerStartRestartGroup.startReplaceGroup(1020066556);
                        ComposerKt.sourceInformation(composerStartRestartGroup, "CC(remember):MainActivity.kt#9igjgp");
                        boolean z5 = (i4 & 7168) == 2048;
                        Object objRememberedValue5 = composerStartRestartGroup.rememberedValue();
                        if (z5 || objRememberedValue5 == Composer.Companion.getEmpty()) {
                            objRememberedValue5 = new Function1() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$$ExternalSyntheticLambda7
                                @Override // kotlin.jvm.functions.Function1
                                public final Object invoke(Object obj) {
                                    return MainActivityKt.SuscTumblerContent$lambda$45$lambda$42$lambda$41(onChangeRequest, mutableFloatState, ((Float) obj).floatValue());
                                }
                            };
                            composerStartRestartGroup.updateRememberedValue(objRememberedValue5);
                        }
                        composerStartRestartGroup.endReplaceGroup();
                        SliderKt.Slider(fSuscTumblerContent$lambda$45$lambda$363, (Function1) objRememberedValue5, modifier7, false, closedFloatingPointRangeRangeTo2, 7, (Function0) null, (SliderColors) null, (MutableInteractionSource) null, composerStartRestartGroup, 196992, 456);
                        composer2 = composerStartRestartGroup;
                        composer2.endReplaceGroup();
                    }
                    SpacerKt.Spacer(SizeKt.height-3ABfNKs(Modifier.Companion, Dp.constructor-impl(f)), composer2, 6);
                    composer2.startReplaceGroup(1020081153);
                    ComposerKt.sourceInformation(composer2, "CC(remember):MainActivity.kt#9igjgp");
                    boolean z6 = (57344 & i4) == 16384;
                    Object objRememberedValue6 = composer2.rememberedValue();
                    if (z6 || objRememberedValue6 == Composer.Companion.getEmpty()) {
                        objRememberedValue6 = new Function0() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$$ExternalSyntheticLambda8
                            @Override // kotlin.jvm.functions.Function0
                            public final Object invoke() {
                                return MainActivityKt.SuscTumblerContent$lambda$45$lambda$44$lambda$43(onWriteRequest);
                            }
                        };
                        composer2.updateRememberedValue(objRememberedValue6);
                    }
                    composer2.endReplaceGroup();
                    Composer composer4 = composer2;
                    ButtonKt.Button((Function0) objRememberedValue6, (Modifier) null, false, (Shape) null, (ButtonColors) null, (ButtonElevation) null, (BorderStroke) null, (PaddingValues) null, (MutableInteractionSource) null, ComposableSingletons$MainActivityKt.INSTANCE.m1788getLambda3$app_release(), composer4, 805306368, 510);
                    composerStartRestartGroup = composer4;
                    composerStartRestartGroup.endReplaceGroup();
                } else {
                    modifier2 = modifier5;
                    composerStartRestartGroup.startReplaceGroup(1557875555);
                    ComposerKt.sourceInformation(composerStartRestartGroup, "493@20488L11,493@20446L69,493@20419L364,500@20800L41,501@20858L27");
                    CardKt.Card((Modifier) null, (Shape) null, CardDefaults.INSTANCE.cardColors-ro_MJ88(MaterialTheme.INSTANCE.getColorScheme(composerStartRestartGroup, MaterialTheme.$stable).getErrorContainer-0d7_KjU(), 0L, 0L, 0L, composerStartRestartGroup, CardDefaults.$stable << 12, 14), (CardElevation) null, (BorderStroke) null, ComposableSingletons$MainActivityKt.INSTANCE.m1789getLambda4$app_release(), composerStartRestartGroup, ProfileVerifier.CompilationStatus.RESULT_CODE_ERROR_CANT_WRITE_PROFILE_VERIFICATION_RESULT_CACHE_FILE, 27);
                    SpacerKt.Spacer(SizeKt.height-3ABfNKs(Modifier.Companion, Dp.constructor-impl(f)), composerStartRestartGroup, 6);
                    ProgressIndicatorKt.CircularProgressIndicator-LxG7B9w((Modifier) null, 0L, 0.0f, 0L, 0, composerStartRestartGroup, 0, 31);
                    composerStartRestartGroup = composerStartRestartGroup;
                    composerStartRestartGroup.endReplaceGroup();
                }
                composerStartRestartGroup.endReplaceGroup();
            }
            ComposerKt.sourceInformationMarkerEnd(composerStartRestartGroup);
            ComposerKt.sourceInformationMarkerEnd(composerStartRestartGroup);
            composerStartRestartGroup.endNode();
            ComposerKt.sourceInformationMarkerEnd(composerStartRestartGroup);
            ComposerKt.sourceInformationMarkerEnd(composerStartRestartGroup);
            ComposerKt.sourceInformationMarkerEnd(composerStartRestartGroup);
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventEnd();
            }
        } else {
            composerStartRestartGroup.skipToGroupEnd();
        }
        ScopeUpdateScope scopeUpdateScopeEndRestartGroup = composerStartRestartGroup.endRestartGroup();
        if (scopeUpdateScopeEndRestartGroup != null) {
            scopeUpdateScopeEndRestartGroup.updateScope(new Function2() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$$ExternalSyntheticLambda9
                @Override // kotlin.jvm.functions.Function2
                public final Object invoke(Object obj, Object obj2) {
                    return MainActivityKt.SuscTumblerContent$lambda$46(z, z2, pair, onChangeRequest, onWriteRequest, onLEDRequest, onRangeRequest, modifier2, i, i2, (Composer) obj, ((Integer) obj2).intValue());
                }
            });
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final boolean SuscTumblerContent$lambda$45$lambda$30(MutableState<Boolean> mutableState) {
        return ((Boolean) ((State) mutableState).getValue()).booleanValue();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final void SuscTumblerContent$lambda$45$lambda$31(MutableState<Boolean> mutableState, boolean z) {
        mutableState.setValue(Boolean.valueOf(z));
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final boolean SuscTumblerContent$lambda$45$lambda$33(MutableState<Boolean> mutableState) {
        return ((Boolean) ((State) mutableState).getValue()).booleanValue();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final void SuscTumblerContent$lambda$45$lambda$34(MutableState<Boolean> mutableState, boolean z) {
        mutableState.setValue(Boolean.valueOf(z));
    }

    private static final float SuscTumblerContent$lambda$45$lambda$36(MutableFloatState mutableFloatState) {
        return ((FloatState) mutableFloatState).getFloatValue();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final Unit SuscTumblerContent$lambda$45$lambda$40$lambda$39(Function1 function1, MutableFloatState mutableFloatState, float f) {
        mutableFloatState.setFloatValue(f);
        function1.invoke(Integer.valueOf((int) SuscTumblerContent$lambda$45$lambda$36(mutableFloatState)));
        return Unit.INSTANCE;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final Unit SuscTumblerContent$lambda$45$lambda$42$lambda$41(Function1 function1, MutableFloatState mutableFloatState, float f) {
        mutableFloatState.setFloatValue(f);
        function1.invoke(Integer.valueOf((int) SuscTumblerContent$lambda$45$lambda$36(mutableFloatState)));
        return Unit.INSTANCE;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final Unit SuscTumblerContent$lambda$45$lambda$44$lambda$43(Function0 function0) {
        function0.invoke();
        return Unit.INSTANCE;
    }

    public static final void FullAppPreview(Composer composer, final int i) {
        Composer composerStartRestartGroup = composer.startRestartGroup(-1165318068);
        ComposerKt.sourceInformation(composerStartRestartGroup, "C(FullAppPreview)517@21341L845:MainActivity.kt#6o5wwo");
        if (i != 0 || !composerStartRestartGroup.getSkipping()) {
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventStart(-1165318068, i, -1, "ru.cyclone.susc_tumbler.FullAppPreview (MainActivity.kt:516)");
            }
            ThemeKt.Susc_tumblerTheme(false, false, ComposableSingletons$MainActivityKt.INSTANCE.m1790getLambda5$app_release(), composerStartRestartGroup, 384, 3);
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventEnd();
            }
        } else {
            composerStartRestartGroup.skipToGroupEnd();
        }
        ScopeUpdateScope scopeUpdateScopeEndRestartGroup = composerStartRestartGroup.endRestartGroup();
        if (scopeUpdateScopeEndRestartGroup != null) {
            scopeUpdateScopeEndRestartGroup.updateScope(new Function2() { // from class: ru.cyclone.susc_tumbler.MainActivityKt$$ExternalSyntheticLambda5
                @Override // kotlin.jvm.functions.Function2
                public final Object invoke(Object obj, Object obj2) {
                    return MainActivityKt.FullAppPreview$lambda$47(i, (Composer) obj, ((Integer) obj2).intValue());
                }
            });
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final byte[] SuscTumbler$lambda$13(State<byte[]> state) {
        return (byte[]) state.getValue();
    }
}
